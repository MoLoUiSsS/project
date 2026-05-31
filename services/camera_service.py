import os
import uuid
import base64
import threading
from config import UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

_socketio = None
_capture_event = threading.Event()
_capture_result = None
_phone_connected = False
_phone_sid = None  # Track the phone's socket session ID

CAPTURE_TIMEOUT = 10


def init(socketio):
    global _socketio
    _socketio = socketio

    @socketio.on('phone_connected')
    def handle_phone_connected():
        global _phone_connected, _phone_sid
        from flask import request as flask_request
        _phone_connected = True
        _phone_sid = flask_request.sid
        print(f"[CAMERA] Phone camera connected (sid={_phone_sid})")
        socketio.emit('camera_status', {'connected': True})

    @socketio.on('phone_disconnected')
    def handle_phone_disconnected():
        global _phone_connected, _phone_sid
        _phone_connected = False
        _phone_sid = None
        print("[CAMERA] Phone camera disconnected (user action)")
        socketio.emit('camera_status', {'connected': False})

    @socketio.on('phone_frame')
    def handle_phone_frame(data):
        """Relay the low-res live preview frame to all admin viewers."""
        if data and data.get('image'):
            socketio.emit('phone_frame', {'image': data['image']})

    @socketio.on('disconnect')
    def handle_disconnect():
        global _phone_connected, _phone_sid
        from flask import request as flask_request
        # Only mark phone as disconnected if the phone's session dropped
        if flask_request.sid == _phone_sid:
            _phone_connected = False
            _phone_sid = None
            print("[CAMERA] Phone session dropped (socket disconnect)")
            socketio.emit('camera_status', {'connected': False})

    @socketio.on('phone_capture_result')
    def handle_capture_result(data):
        global _capture_result
        if data and data.get('image'):
            try:
                img_data = data['image']
                if ',' in img_data:
                    img_data = img_data.split(',')[1]

                img_bytes = base64.b64decode(img_data)
                filename = f"parking_{uuid.uuid4().hex[:8]}.jpg"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                with open(filepath, 'wb') as f:
                    f.write(img_bytes)

                _capture_result = filepath
                print(f"[CAMERA] Phone capture saved: {filepath}")
            except Exception as e:
                print(f"[CAMERA] Error saving phone capture: {e}")
                _capture_result = None
        else:
            _capture_result = None

        _capture_event.set()

    @socketio.on('manual_phone_capture')
    def handle_manual_capture(data):
        if data and data.get('image'):
            try:
                img_data = data['image']
                if ',' in img_data:
                    img_data = img_data.split(',')[1]

                img_bytes = base64.b64decode(img_data)
                filename = f"parking_{uuid.uuid4().hex[:8]}.jpg"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                with open(filepath, 'wb') as f:
                    f.write(img_bytes)

                print(f"[CAMERA] Manual phone capture saved: {filepath}")
                from services import gate_service
                gate_service.handle_manual_phone_capture(filepath)
            except Exception as e:
                print(f"[CAMERA] Error saving manual phone capture: {e}")


def is_phone_connected():
    return _phone_connected


def capture():
    global _capture_result

    if _phone_connected and _socketio:
        return _capture_from_phone()

    print("[CAMERA] Error: Phone camera not connected")
    return None


def _capture_from_phone():
    global _capture_result

    _capture_event.clear()
    _capture_result = None

    print("[CAMERA] Requesting capture from phone...")
    _socketio.emit('request_capture', {})

    _capture_event.wait(timeout=CAPTURE_TIMEOUT)

    if _capture_result:
        return _capture_result

    print("[CAMERA] Phone capture timed out")
    return None
