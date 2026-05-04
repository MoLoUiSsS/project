import os
import uuid
import datetime
from flask import Blueprint, request, jsonify
from database import get_db_connection
from services import arduino_service, ocr_service, camera_service, gate_service
from config import UPLOAD_FOLDER

_socketio = None
parking_bp = Blueprint('parking', __name__)


def init(socketio):
    global _socketio
    _socketio = socketio


@parking_bp.route('/api/gate/capture', methods=['POST'])
def gate_capture():
    image_path = None

    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = f"parking_{uuid.uuid4().hex[:8]}.jpg"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(image_path)

    if not image_path:
        image_path = camera_service.capture()

    if not image_path:
        return jsonify({'success': False, 'error': 'No image captured'}), 500

    plate, reliability = ocr_service.process_plate(image_path)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    relative_path = image_path.replace('static/', '') if 'static/' in image_path else image_path

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

    access_granted, reason = gate_service.check_plate_access(plate)

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

    result = {
        'success': True,
        'access': access_granted,
        'plate': plate,
        'reliability': reliability,
        'reason': reason,
        'image': relative_path,
        'timestamp': timestamp
    }

    if _socketio:
        _socketio.emit('gate_result', result)
        _socketio.emit('new_capture', {
            'plaque_immatriculation': plate,
            'fiabilite_lecture': reliability,
            'date_heure_capture': timestamp,
            'chemin_image': relative_path
        })

    return jsonify(result)


@parking_bp.route('/api/check-plate', methods=['POST'])
def check_plate():
    data = request.get_json()
    if not data or not data.get('plate'):
        return jsonify({'success': False, 'error': 'No plate provided'}), 400

    access, reason = gate_service.check_plate_access(data['plate'])
    return jsonify({'success': True, 'access': access, 'reason': reason})


@parking_bp.route('/api/access-logs')
def get_access_logs():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 100")
            return jsonify([dict(row) for row in cursor.fetchall()])
        finally:
            conn.close()
    return jsonify([])
