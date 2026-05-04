"""
Arduino Diagnostic Script
Run this ALONE (close app.py first!) to test if:
  1. Python can find the Arduino port
  2. The sensor is sending data
  3. The gate commands work
"""

import serial
import serial.tools.list_ports
import threading
import time
import re

# ─── STEP 1: List all available COM ports ───────────────────────
print("\n" + "="*50)
print("  ARDUINO DIAGNOSTIC TOOL")
print("="*50)

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("\n❌ NO serial ports found at all!")
    print("   → Is the Arduino plugged in via USB?")
    input("\nPress Enter to exit...")
    exit()

print(f"\n✅ Found {len(ports)} serial port(s):")
for i, p in enumerate(ports):
    print(f"   [{i}] {p.device}  —  {p.description}")

# ─── STEP 2: Pick the port ──────────────────────────────────────
port = None

for p in ports:
    desc = (p.description or "").lower()
    if any(kw in desc for kw in ['arduino', 'ch340', 'cp210', 'ftdi', 'usb serial', 'usb-serial', 'usb', 'périphérique']):
        port = p.device
        print(f"\n✅ Auto-detected Arduino on: {port}")
        break

if not port:
    print(f"\n⚠️  Could not auto-detect Arduino.")
    choice = input(f"   Enter port index (0-{len(ports)-1}) or full name (e.g. COM3): ").strip()
    try:
        port = ports[int(choice)].device
    except (ValueError, IndexError):
        port = choice

# ─── STEP 3: Connect and listen ─────────────────────────────────
print(f"\n🔌 Connecting to {port} at 9600 baud...")

try:
    ser = serial.Serial(port, 9600, timeout=2)
    print(f"   Waiting 2s for Arduino to reset...")
    time.sleep(2)
    print(f"\n✅ Connected! Listening for data (Ctrl+C to stop)...\n")
    print("-"*50)
    print("  Commands you can type:")
    print("  GATE:OPEN   — opens the servo gate")
    print("  GATE:CLOSE  — closes the servo gate")
    print("  q           — quit")
    print("-"*50 + "\n")

    # Use a list to share state between threads (avoids nonlocal issues)
    state = {'gate_open': False}

    def extract_distance(line):
        """
        Handles two formats:
          - Parking sketch:  "DIST:24"
          - Test sketch:     "Distance: 24.83 cm"
        Returns float distance or None.
        """
        # Format 1: DIST:24
        if line.startswith("DIST:"):
            try:
                return float(line.split(":")[1])
            except ValueError:
                return None

        # Format 2: "Distance: 24.83 cm" or "Distance: 24.83cm"
        match = re.search(r'distance[:\s]+([0-9]+\.?[0-9]*)', line, re.IGNORECASE)
        if match:
            return float(match.group(1))

        return None

    def read_serial():
        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue

                    dist = extract_distance(line)

                    if dist is not None:
                        print(f"📡 Distance: {dist:.1f} cm")

                        # Auto gate logic
                        if dist <= 30 and not state['gate_open']:
                            state['gate_open'] = True
                            ser.write(b"GATE:OPEN\n")
                            print(f"🚨 Distance ≤ 30cm → Sending GATE:OPEN")

                        elif dist > 40 and state['gate_open']:
                            state['gate_open'] = False
                            ser.write(b"GATE:CLOSE\n")
                            print(f"✅ Clear → Sending GATE:CLOSE")

                    elif line == "CAR_DETECTED":
                        print(f"🚗 CAR DETECTED!")
                    elif line == "GATE_OPENED":
                        print(f"🟢 Gate OPENED")
                    elif line == "GATE_CLOSED":
                        print(f"🔴 Gate CLOSED")
                    elif line == "PARKING_SYSTEM_READY":
                        print(f"✅ Arduino Ready!")
                    else:
                        print(f"[RAW] {line}")

                time.sleep(0.05)
            except Exception as e:
                print(f"Read error: {e}")
                break

    t = threading.Thread(target=read_serial, daemon=True)
    t.start()

    # Main thread handles user input
    while True:
        cmd = input()
        if cmd.strip().lower() == 'q':
            break
        if cmd.strip():
            ser.write(f"{cmd.strip()}\n".encode())
            print(f"→ Sent: {cmd.strip()}")

    ser.close()
    print("Disconnected.")

except serial.SerialException as e:
    print(f"\n❌ Could not open {port}: {e}")
    print("\n   Possible reasons:")
    print("   1. app.py is still running and using the port → close it first")
    print("   2. Wrong COM port selected")
    print("   3. Arduino not plugged in")

input("\nPress Enter to exit...")
