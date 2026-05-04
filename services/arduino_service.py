import time
import re
import threading
from config import SERIAL_BAUD_RATE, SERIAL_KEYWORDS, DETECTION_DISTANCE, CLEAR_DISTANCE

arduino_serial = None
arduino_thread = None
arduino_running = False
arduino_port = None
last_distance = -1
detection_cooldown = False

_socketio = None
_on_car_detected = None


def init(socketio, on_car_detected_callback):
    global _socketio, _on_car_detected
    _socketio = socketio
    _on_car_detected = on_car_detected_callback


def get_status():
    if arduino_serial and arduino_serial.is_open:
        return {"connected": True, "port": arduino_port, "last_distance": last_distance}
    return {"connected": False, "port": None, "last_distance": last_distance}


def connect(port=None):
    global arduino_serial, arduino_thread, arduino_running, arduino_port

    try:
        import serial
        import serial.tools.list_ports
    except ImportError:
        return False, "pyserial not installed"

    if arduino_serial and arduino_serial.is_open:
        arduino_running = False
        time.sleep(1)
        arduino_serial.close()

    if not port:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            if any(kw in desc for kw in SERIAL_KEYWORDS):
                port = p.device
                break
        if not port and ports:
            port = ports[0].device

    if not port:
        return False, "No serial port found"

    try:
        arduino_serial = serial.Serial(port, SERIAL_BAUD_RATE, timeout=1)
        arduino_port = port
        time.sleep(2)

        arduino_running = True
        arduino_thread = threading.Thread(target=_reader_thread, daemon=True)
        arduino_thread.start()

        print(f"Arduino connected on {port}")
        if _socketio:
            _socketio.emit('arduino_status', {'connected': True, 'port': port})
        return True, f"Connected on {port}"
    except Exception as e:
        print(f"Arduino connection error: {e}")
        return False, str(e)


def disconnect():
    global arduino_serial, arduino_running
    arduino_running = False
    if arduino_serial and arduino_serial.is_open:
        arduino_serial.close()
    arduino_serial = None
    if _socketio:
        _socketio.emit('arduino_status', {'connected': False, 'port': None})


def send_command(command):
    if arduino_serial and arduino_serial.is_open:
        try:
            arduino_serial.write(f"{command}\n".encode())
        except Exception as e:
            print(f"Error sending to Arduino: {e}")


def list_ports():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [{'device': p.device, 'description': p.description} for p in ports]
    except ImportError:
        return []


def _parse_distance(line):
    if line.startswith("DIST:"):
        try:
            return float(line.split(":")[1])
        except (ValueError, IndexError):
            return None
    match = re.search(r'distance[:\s]+([0-9]+\.?[0-9]*)', line, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _reader_thread():
    global arduino_serial, arduino_running, last_distance, detection_cooldown

    gate_state = [False]

    while arduino_running and arduino_serial and arduino_serial.is_open:
        try:
            if arduino_serial.in_waiting > 0:
                line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                dist = _parse_distance(line)

                if dist is not None:
                    last_distance = dist
                    if _socketio:
                        _socketio.emit('distance_update', {'distance': round(dist, 1)})

                    if dist <= DETECTION_DISTANCE and not gate_state[0] and not detection_cooldown:
                        gate_state[0] = True
                        detection_cooldown = True
                        if _socketio:
                            _socketio.emit('gate_triggered', {
                                'message': 'Véhicule détecté ! Analyse en cours...'
                            })
                        if _on_car_detected:
                            threading.Thread(target=_on_car_detected, daemon=True).start()

                    elif dist > CLEAR_DISTANCE:
                        gate_state[0] = False

                elif line == "CAR_DETECTED":
                    if _socketio:
                        _socketio.emit('gate_triggered', {
                            'message': 'Car detected! Capturing...'
                        })
                    if not detection_cooldown and _on_car_detected:
                        detection_cooldown = True
                        threading.Thread(target=_on_car_detected, daemon=True).start()

                elif line == "GATE_OPENED":
                    if _socketio:
                        _socketio.emit('gate_status', {'status': 'open'})

                elif line == "GATE_CLOSED":
                    if _socketio:
                        _socketio.emit('gate_status', {'status': 'closed'})
                    detection_cooldown = False

                elif line == "PARKING_SYSTEM_READY":
                    if _socketio:
                        _socketio.emit('arduino_status', {
                            'connected': True, 'port': arduino_port, 'message': 'System Ready'
                        })

            time.sleep(0.05)
        except Exception as e:
            print(f"Serial read error: {e}")
            time.sleep(1)

    if _socketio:
        _socketio.emit('arduino_status', {'connected': False, 'port': None})
