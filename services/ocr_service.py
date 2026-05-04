import os
import re
import json
import base64
import random
import time
import urllib.request
import urllib.parse
from config import OCR_API_URL, OCR_API_KEY, OCR_TIMEOUT

VALID_WILAYAS = set(f"{i:02d}" for i in range(1, 59))


def process_plate(image_path):
    enhanced_path = _preprocess_image(image_path)
    work_path = enhanced_path or image_path

    for engine in ['2', '1']:
        plate, reliability = _ocr_attempt(work_path, engine)
        if plate and plate != "NOT FOUND":
            return plate, reliability

    if enhanced_path and enhanced_path != image_path:
        for engine in ['2', '1']:
            plate, reliability = _ocr_attempt(image_path, engine)
            if plate and plate != "NOT FOUND":
                return plate, reliability

    return "NOT FOUND", 0.0


def _preprocess_image(image_path):
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        denoised = cv2.bilateralFilter(enhanced, 11, 17, 17)

        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)

        base, ext = os.path.splitext(image_path)
        enhanced_path = f"{base}_enhanced{ext}"
        cv2.imwrite(enhanced_path, sharpened, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return enhanced_path

    except ImportError:
        return None
    except Exception as e:
        print(f"Preprocessing error: {e}")
        return None


def _ocr_attempt(image_path, engine):
    try:
        with open(image_path, "rb") as f:
            base64_img = base64.b64encode(f.read()).decode('utf-8')

        params = {
            'apikey': OCR_API_KEY,
            'base64Image': 'data:image/jpeg;base64,' + base64_img,
            'isOverlayRequired': 'false',
            'OCREngine': engine,
            'scale': 'true',
            'isTable': 'false',
        }

        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(OCR_API_URL, data=data)

        with urllib.request.urlopen(req, timeout=OCR_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))

            if result.get('IsErroredOnProcessing') or not result.get('ParsedResults'):
                return None, 0.0

            text = result['ParsedResults'][0]['ParsedText'].replace('\r\n', ' ').strip()
            print(f"[OCR Engine {engine}] Raw: {text}")

            return _parse_plate(text)

    except Exception as e:
        print(f"OCR Engine {engine} error: {e}")
        return None, 0.0


def _parse_plate(text):
    text_fixed = text.replace('O', '0').replace('o', '0')
    text_fixed = text_fixed.replace('I', '1').replace('l', '1')
    text_fixed = text_fixed.replace('S', '5').replace('s', '5')
    text_fixed = text_fixed.replace('B', '8').replace('G', '6')
    text_fixed = text_fixed.replace('Z', '2').replace('z', '2')
    text_fixed = text_fixed.replace('T', '7').replace('A', '4')

    clean = re.sub(r'[^\d\s\-/|]', ' ', text_fixed)
    clean = re.sub(r'[\-/|]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    match = re.search(r'(\d{4,6})\s+(\d{3})\s+(\d{2})', clean)
    if match:
        plate = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        wilaya = match.group(3)
        conf = 98.0 if wilaya in VALID_WILAYAS else 80.0
        return plate, conf

    match = re.search(r'(\d{4,6})\s*(\d{3})\s*(\d{2})', clean)
    if match:
        plate = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        wilaya = match.group(3)
        conf = 92.0 if wilaya in VALID_WILAYAS else 75.0
        return plate, conf

    digits_only = re.sub(r'\D', '', text_fixed)
    if len(digits_only) >= 9:
        wilaya = digits_only[-2:]
        middle = digits_only[-5:-2]
        matricule = digits_only[:-5]
        if len(matricule) > 6:
            matricule = matricule[-6:]
        if len(matricule) >= 4 and len(middle) == 3:
            plate = f"{matricule} {middle} {wilaya}"
            conf = 85.0 if wilaya in VALID_WILAYAS else 70.0
            return plate, conf

    if len(digits_only) > 0:
        return text[:20], 50.0

    return None, 0.0


def _generate_mock_plate():
    time.sleep(1)
    matricule = f"{random.randint(10000, 99999)}"
    veh_type = random.randint(1, 4)
    year = random.randint(0, 24)
    middle = f"{veh_type}{year:02d}"
    wilaya_code = f"{random.randint(1, 58):02d}"
    plate = f"{matricule} {middle} {wilaya_code}"
    reliability = round(random.uniform(75.0, 90.0), 2)
    return plate, reliability
