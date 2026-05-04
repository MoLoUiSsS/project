import re
import time
import datetime
from database import get_db_connection
from services import arduino_service, ocr_service, camera_service
from config import DETECTION_COOLDOWN

_socketio = None


def init(socketio):
    global _socketio
    _socketio = socketio


def check_plate_access(plate):
    conn = get_db_connection()
    if not conn:
        return False, "Database error"

    try:
        cursor = conn.cursor()
        plate_clean = re.sub(r'\s+', ' ', plate.strip())
        cursor.execute(
            "SELECT * FROM registered_vehicles "
            "WHERE REPLACE(plaque_immatriculation, ' ', '') = REPLACE(?, ' ', '')",
            (plate_clean,)
        )
        vehicle = cursor.fetchone()

        if not vehicle:
            return False, "Véhicule non enregistré"
        if not vehicle['is_paid']:
            return False, "Frais de parking non payés"
        return True, f"Accès autorisé — {vehicle['owner_name']}"
    finally:
        conn.close()


def handle_car_detection():
    try:
        image_path = camera_service.capture()
        if not image_path:
            if _socketio:
                _socketio.emit('gate_result', {
                    'access': False, 'plate': 'N/A',
                    'reason': 'Webcam capture failed', 'image': ''
                })
            arduino_service.detection_cooldown = False
            return

        plate, reliability = ocr_service.process_plate(image_path)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        relative_path = image_path.replace('static/', '')

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO captures (plaque_immatriculation, date_heure_capture, "
                    "chemin_image, fiabilite_lecture, id_camera) VALUES (?, ?, ?, ?, ?)",
                    (plate, timestamp, relative_path, reliability, 1)
                )
                conn.commit()
            finally:
                conn.close()

        if _socketio:
            _socketio.emit('new_capture', {
                'plaque_immatriculation': plate,
                'fiabilite_lecture': reliability,
                'date_heure_capture': timestamp,
                'chemin_image': relative_path
            })

        access_granted, reason = check_plate_access(plate)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO access_logs (plaque_immatriculation, timestamp, "
                    "access_granted, reason, chemin_image, distance_cm) VALUES (?, ?, ?, ?, ?, ?)",
                    (plate, timestamp, 1 if access_granted else 0, reason,
                     relative_path, arduino_service.last_distance)
                )
                conn.commit()
            finally:
                conn.close()

        if access_granted:
            arduino_service.send_command("GATE:OPEN")
        else:
            arduino_service.send_command("GATE:CLOSE")

        if _socketio:
            _socketio.emit('gate_result', {
                'access': access_granted,
                'plate': plate,
                'reliability': reliability,
                'reason': reason,
                'image': relative_path,
                'timestamp': timestamp,
                'distance': arduino_service.last_distance
            })

        time.sleep(DETECTION_COOLDOWN)
        arduino_service.detection_cooldown = False

    except Exception as e:
        print(f"Error in car detection handler: {e}")
        arduino_service.detection_cooldown = False
