import os
import re
import json
import base64
import random
import time
import urllib.request
import urllib.parse
from config import OCR_API_URL, OCR_API_KEY, OCR_TIMEOUT

# Load backup key if defined
try:
    from config import OCR_API_KEY_2
except ImportError:
    OCR_API_KEY_2 = None

VALID_WILAYAS = set(f"{i:02d}" for i in range(1, 59))

# Track rate-limited keys to skip them temporarily
_rate_limited_keys = {}
RATE_LIMIT_COOLDOWN = 3600  # 1 hour cooldown before retrying a key


def _get_active_keys():
    """Return API keys that are not currently rate-limited."""
    now = time.time()
    keys = [OCR_API_KEY]
    if OCR_API_KEY_2 and OCR_API_KEY_2 != 'helloworld':
        keys.append(OCR_API_KEY_2)

    active = []
    for k in keys:
        limited_at = _rate_limited_keys.get(k)
        if limited_at is None or (now - limited_at) > RATE_LIMIT_COOLDOWN:
            active.append(k)
    return active if active else keys  # fallback: use all keys even if limited


def process_plate(image_path):
    enhanced_path = _preprocess_image(image_path)
    work_path = enhanced_path or image_path

    # Try enhanced image first with all active keys and both OCR engines
    for api_key in _get_active_keys():
        for engine in ['2', '1']:
            plate, reliability = _ocr_attempt(work_path, engine, api_key)
            if plate and plate != "NOT FOUND":
                print(f"[OCR] SUCCESS with engine={engine} key=...{api_key[-4:]}: {plate}")
                return plate, reliability

    # Retry on original image (before enhancement) if enhanced failed
    if enhanced_path and enhanced_path != image_path:
        for api_key in _get_active_keys():
            for engine in ['2', '1']:
                plate, reliability = _ocr_attempt(image_path, engine, api_key)
                if plate and plate != "NOT FOUND":
                    print(f"[OCR] SUCCESS (original) engine={engine}: {plate}")
                    return plate, reliability

    # Final fallback: local Tesseract (works offline, no API needed)
    plate, reliability = _tesseract_fallback(work_path)
    if plate:
        print(f"[OCR] Tesseract fallback result: {plate}")
        return plate, reliability

    print("[OCR] All methods failed — NOT FOUND")
    return "NOT FOUND", 0.0


def _preprocess_image(image_path):
    """Server-side image enhancement using OpenCV if available."""
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            return None

        # Upscale small images for better OCR accuracy
        h, w = img.shape[:2]
        if w < 800:
            scale = 800 / w
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # CLAHE for adaptive contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Bilateral filter (preserve edges, reduce noise)
        denoised = cv2.bilateralFilter(enhanced, 11, 17, 17)

        # Sharpen
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)

        base, ext = os.path.splitext(image_path)
        enhanced_path = f"{base}_enhanced{ext}"
        cv2.imwrite(enhanced_path, sharpened, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return enhanced_path

    except ImportError:
        return None
    except Exception as e:
        print(f"[OCR] Preprocessing error: {e}")
        return None


def _ocr_attempt(image_path, engine, api_key):
    """Single OCR attempt using OCR.space API."""
    try:
        with open(image_path, "rb") as f:
            base64_img = base64.b64encode(f.read()).decode('utf-8')

        params = {
            'apikey': api_key,
            'base64Image': 'data:image/jpeg;base64,' + base64_img,
            'isOverlayRequired': 'false',
            'OCREngine': engine,
            'scale': 'true',
            'isTable': 'false',
            'detectOrientation': 'true',
        }

        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(OCR_API_URL, data=data)
        req.add_header('User-Agent', 'ParkNet/1.0')

        with urllib.request.urlopen(req, timeout=OCR_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Detect rate-limiting
            if result.get('IsErroredOnProcessing'):
                err_msg = result.get('ErrorMessage', [''])[0] if isinstance(result.get('ErrorMessage'), list) else str(result.get('ErrorMessage', ''))
                print(f"[OCR] Engine {engine} error: {err_msg}")
                if 'limit' in err_msg.lower() or 'exceeded' in err_msg.lower() or 'quota' in err_msg.lower():
                    _rate_limited_keys[api_key] = time.time()
                    print(f"[OCR] Key ...{api_key[-4:]} rate-limited, marking for cooldown")
                return None, 0.0

            if not result.get('ParsedResults'):
                return None, 0.0

            text = result['ParsedResults'][0]['ParsedText'].replace('\r\n', ' ').replace('\n', ' ').strip()
            print(f"[OCR] Engine {engine} raw text: '{text}'")

            return _parse_plate(text)

    except Exception as e:
        print(f"[OCR] Engine {engine} exception: {e}")
        return None, 0.0


def _tesseract_fallback(image_path):
    """Local Tesseract OCR — works offline, no API quota."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)

        # Try multiple PSM modes for best plate reading
        configs = [
            '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ',
            '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ',
            '--oem 3 --psm 6',
        ]

        for cfg in configs:
            text = pytesseract.image_to_string(img, config=cfg).strip()
            if text:
                print(f"[Tesseract] Raw: '{text}'")
                plate, conf = _parse_plate(text)
                if plate:
                    return plate, max(conf - 10, 40.0)  # Slight confidence penalty vs API

        return None, 0.0

    except ImportError:
        print("[OCR] Tesseract not installed (pip install pytesseract pillow)")
        return None, 0.0
    except Exception as e:
        print(f"[Tesseract] Error: {e}")
        return None, 0.0


def _parse_plate(text):
    """
    Parse Algerian license plate from OCR raw text.
    Format: XXXXX NNN WW  (5 digits, 2-3 middle, 2 wilaya code)
    Examples: 53872 00 16 / 12345 100 16 / 98765 216 31
    """
    if not text:
        return None, 0.0

    # Step 1: Fix common OCR character confusions
    text_fixed = text.upper()
    text_fixed = text_fixed.replace('O', '0').replace('Q', '0').replace('D', '0')
    text_fixed = text_fixed.replace('I', '1').replace('L', '1').replace('|', '1')
    text_fixed = text_fixed.replace('S', '5').replace('Z', '2')
    text_fixed = text_fixed.replace('B', '8').replace('G', '6')
    text_fixed = text_fixed.replace('T', '7').replace('A', '4')

    # Step 2: Keep only digits and separators
    clean = re.sub(r'[^\d\s\-/|]', ' ', text_fixed)
    clean = re.sub(r'[\-/|]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Step 3: Try strict spaced pattern first (most reliable)
    match = re.search(r'\b(\d{4,6})\s+(\d{2,3})\s+(\d{2})\b', clean)
    if match:
        plate = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        wilaya = match.group(3)
        conf = 98.0 if wilaya in VALID_WILAYAS else 80.0
        return plate, conf

    # Step 4: Relaxed pattern (no mandatory spaces)
    match = re.search(r'(\d{4,6})\s*(\d{2,3})\s*(\d{2})', clean)
    if match:
        plate = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        wilaya = match.group(3)
        conf = 88.0 if wilaya in VALID_WILAYAS else 70.0
        return plate, conf

    # Step 5: Digit-only reconstruction (last resort)
    digits_only = re.sub(r'\D', '', text_fixed)
    if len(digits_only) >= 8:
        # Try all valid splits: [4..6] + [2..3] + [2]
        for mat_len in [5, 6, 4]:
            for mid_len in [3, 2]:
                wil_len = 2
                needed = mat_len + mid_len + wil_len
                if len(digits_only) >= needed:
                    segment = digits_only[:needed]
                    mat = segment[:mat_len]
                    mid = segment[mat_len:mat_len + mid_len]
                    wil = segment[mat_len + mid_len:]
                    if len(mat) >= 4 and wil in VALID_WILAYAS:
                        plate = f"{mat} {mid} {wil}"
                        return plate, 82.0

        # Absolute fallback: take last 9 digits and split 5+2+2
        if len(digits_only) >= 9:
            d = digits_only[-9:]
            plate = f"{d[:5]} {d[5:7]} {d[7:9]}"
            wilaya = d[7:9]
            conf = 72.0 if wilaya in VALID_WILAYAS else 55.0
            return plate, conf

    # Step 6: Return raw text if it has any digits (very low confidence)
    if re.search(r'\d', text_fixed):
        return text[:20].strip(), 40.0

    return None, 0.0
