import os
import uuid
import time
import threading
from config import UPLOAD_FOLDER

_webcam_lock = threading.Lock()

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def capture():
    with _webcam_lock:
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Cannot open webcam")
                return None

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

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
                print(f"Captured frame (sharpness: {best_sharpness:.1f})")
                return filepath
            else:
                print("Error: Failed to capture frame")
                return None

        except ImportError:
            print("OpenCV not installed. Run: pip install opencv-python")
            return None
        except Exception as e:
            print(f"Webcam capture error: {e}")
            return None
