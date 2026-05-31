from flask import Flask
from flask_socketio import SocketIO
from config import SECRET_KEY
from database import setup_database
import socket

def get_local_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    
    try:
        host_name = socket.gethostname()
        for ip in socket.gethostbyname_ex(host_name)[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
        
    return ips if ips else ["127.0.0.1"]


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

from routes.pages import pages_bp
from routes.capture_routes import capture_bp, init as init_captures
from routes.vehicle_routes import vehicle_bp, init as init_vehicles
from routes.parking_routes import parking_bp, init as init_parking
from routes.arduino_routes import arduino_bp
from routes.analytics_routes import analytics_bp

app.register_blueprint(pages_bp)
app.register_blueprint(capture_bp)
app.register_blueprint(vehicle_bp)
app.register_blueprint(parking_bp)
app.register_blueprint(arduino_bp)
app.register_blueprint(analytics_bp)

from services import arduino_service, gate_service, camera_service

init_captures(socketio)
init_vehicles(socketio)
init_parking(socketio)
gate_service.init(socketio)
camera_service.init(socketio)
arduino_service.init(socketio, gate_service.handle_car_detection)

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  PARKNET — SMART IoT PARKING PLATFORM")
    print("=" * 50)

    setup_database()

    try:
        success, msg = arduino_service.connect()
        if success:
            print(f"  Arduino: Connected ({msg})")
        else:
            print(f"  Arduino: Not connected ({msg})")
    except Exception as e:
        print(f"  Arduino: Skipped ({e})")

    print(f"\n  Dashboard:    http://localhost:5000/")
    print(f"  Parking Gate: http://localhost:5000/parking")
    print(f"  Register:     http://localhost:5000/register")
    print(f"  Admin Panel:  http://localhost:5000/admin")
    
    print("\n  [PHONE] CAMERA LINKS (open on your phone browser):")
    for ip in get_local_ips():
        print(f"  -> http://{ip}:5000/camera")
    print("=" * 50 + "\n")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
