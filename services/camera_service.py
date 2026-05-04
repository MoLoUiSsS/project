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

CAPTURE_TIMEOUT = 10


def init(socketio):
    global _socketio
    _socketio = socketio

    @socketio.on('phone_connected')
    def handle_phone_connected():
        global _phone_connected
        _phone_connected = True
        print("[CAMERA] Phone camera connected")
        socketio.emit('camera_status', {'connected': True})

    @socketio.on('phone_disconnected')
    def handle_phone_disconnected():
        global _phone_connected
        _phone_connected = False
        print("[CAMERA] Phone camera disconnected")
        socketio.emit('camera_status', {'connected': False})

    @socketio.on('disconnect')
    def handle_disconnect():
        global _phone_connected
        _phone_connected = False

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


def is_phone_connected():
    return _phone_connected


def capture():
    global _capture_result

    if _phone_connected and _socketio:
        return _capture_from_phone()

    return _capture_from_webcam()


def _capture_from_phone():
    global _capture_result

    _capture_event.clear()
    _capture_result = None

    print("[CAMERA] Requesting capture from phone...")
    _socketio.emit('request_capture', {})

    _capture_event.wait(timeout=CAPTURE_TIMEOUT)

    if _capture_result:
        return _capture_result

    print("[CAMERA] Phone capture timed out, falling back to webcam")
    return _capture_from_webcam()


def _capture_from_webcam():
    try:
        import cv2
        import time

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[CAMERA] Cannot open webcam")
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        time.sleep(1.0)

        best_frame = None
        best_sharpness = -1

        for _ in range(15):
            ret, frame = cap.read()
            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                if sharpness > best_sharpness:
                    best_sharpness = sharpness
                    best_frame = frame.copy()

        cap.release()

        if best_frame is not None:
            filename = f"parking_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            cv2.imwrite(filepath, best_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return filepath

        return None

    except ImportError:
        print("[CAMERA] OpenCV not installed")
        return None
    except Exception as e:
        print(f"[CAMERA] Webcam error: {e}")
        return None
