import os
import uuid
import random
import datetime
from flask import Blueprint, request, jsonify
from database import get_db_connection
from services import ocr_service
from config import UPLOAD_FOLDER

_socketio = None
capture_bp = Blueprint('captures', __name__)


def init(socketio):
    global _socketio
    _socketio = socketio


@capture_bp.route('/upload', methods=['POST'])
def handle_upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    plate, reliability = ocr_service.process_plate(filepath)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    capture_id = random.randint(1000, 9999)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO captures (plaque_immatriculation, date_heure_capture, "
                "chemin_image, fiabilite_lecture, id_camera) VALUES (?, ?, ?, ?, ?)",
                (plate, timestamp, f"uploads/{filename}", reliability, 1)
            )
            conn.commit()
            capture_id = cursor.lastrowid
        finally:
            conn.close()

    capture_data = {
        'id_capture': capture_id,
        'plaque_immatriculation': plate,
        'fiabilite_lecture': reliability,
        'date_heure_capture': timestamp,
        'chemin_image': f"uploads/{filename}"
    }

    if _socketio:
        _socketio.emit('new_capture', capture_data)

    return jsonify({'success': True, 'data': capture_data})


@capture_bp.route('/api/captures')
def get_captures():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM captures ORDER BY date_heure_capture DESC LIMIT 50")
            return jsonify([dict(row) for row in cursor.fetchall()])
        finally:
            conn.close()
    return jsonify([])


@capture_bp.route('/api/captures/<int:capture_id>', methods=['DELETE'])
def delete_capture(capture_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM captures WHERE id_capture = ?", (capture_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Capture not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500
