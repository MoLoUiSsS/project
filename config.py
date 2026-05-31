SECRET_KEY = 'secret!'
DB_FILE = 'lapi_db.sqlite'
UPLOAD_FOLDER = 'static/uploads'

OCR_API_URL = 'https://api.ocr.space/parse/image'
OCR_API_KEY = 'K86410851188957'          # Primary key (personal, 25k/month)
OCR_API_KEY_2 = 'helloworld'             # Add a 2nd key here if you get one
OCR_TIMEOUT = 15

SERIAL_BAUD_RATE = 9600
DETECTION_DISTANCE = 30
CLEAR_DISTANCE = 40
DETECTION_COOLDOWN = 8

SERIAL_KEYWORDS = [
    'arduino', 'ch340', 'cp210', 'ftdi',
    'usb serial', 'usb-serial', 'usb', 'périphérique'
]
