# Comprehensive Description of the LAPI (License Plate Recognition) Application for Algerian Plates

**Context:**
I have built a web-based Intelligent License Plate Recognition (LAPI - Lecture Automatique de Plaques d'Immatriculation) application. It is specifically designed to read, parse, and organize Algerian vehicle license plates in real-time. 

Here is the complete breakdown of the architecture, tech stack, data flow, OCR cleaning logic, and database structure. You can use this as full context for any future development.

---

### 1. Technological Stack (Tools Used)
The application uses a modern, decoupled client-server architecture:
*   **Backend:** Python 3.x using the **Flask** micro-framework.
*   **Real-time Communication:** **Socket.IO** (via `Flask-SocketIO`) to push new captures to all connected clients dynamically without requiring HTTP polling.
*   **Image Processing & OCR:** The system interfaces with the **Free OCR API** (`api.ocr.space`), sending base64-encoded images to Engine 2 for deep-learning-based character extraction.
*   **Database:** **SQLite3** for lightweight, zero-configuration persistence.
*   **Frontend:** Pure HTML5, CSS3 (implementing a modern dark-mode Glassmorphism design), and **Vanilla JavaScript (ES6)**. No heavy frameworks (like React/Angular) are used; DOM manipulation is handled natively.

---

### 2. Database Structure (SQLite `captures` table)
The persistence layer relies on a single relational schema (`lapi_db.sqlite`) optimized to store immutable capture logs:
*   `id_capture` (INTEGER): Primary Key, auto-incremented.
*   `plaque_immatriculation` (TEXT): The final, cleaned, and formatted plate string (e.g., "56789 120 34").
*   `date_heure_capture` (TEXT): Timestamp of the capture.
*   `chemin_image` (TEXT): Relative URL to the saved image in the `static/uploads` folder.
*   `fiabilite_lecture` (REAL): OCR confidence/reliability percentage.
*   `id_camera` (INTEGER): Identifier for the source device.

---

### 3. OCR Catching & Cleaning Logic (Backend - Python)
OCR engines often return noisy text due to dirt, reflections, or angles on physical plates. The backend implements a strict Python Pipeline before database insertion:

1.  **Sanitization Phase:** All non-alphanumeric characters (except spaces and hyphens) are stripped violently using regex: `re.sub(r'[^\d\s\-]', ' ', text)`.
2.  **Primary Regex Match:** The system searches for the exact signature of an Algerian license plate using the pattern: `(\d{4,6})[\s\-]+(\d{3})[\s\-]+(\d{2})`. If matched, the plate is perfectly formatted.
3.  **Fallback Heuristic Phase:** If the hyphen was obstructed and the primary match fails, a secondary fallback triggers. It strips *everything* except digits using `re.sub(r'\D', '', text)`. If the resulting string has 9 or more digits, it rebuilds the plate from right-to-left:
    *   Last 2 digits = Wilaya Code.
    *   Preceding 3 digits = Middle Sequence (Type & Year).
    *   Remaining left digits = Matricule.

---

### 4. Metadata Parsing: Decoding Wilaya, Year, and Type (Frontend - JS)
When the backend broadcasts a clean string like `56789 120 34` via WebSockets, the Frontend JavaScript (`parseAlgerianPlate()`) decrypts this intelligence:

*   **Wilaya Recognition (The "34"):** The right-most 2-digit block. A hardcoded JS dictionary maps codes "01" through "58" (e.g., 16 = Alger, 31 = Oran). If the code is > 58 but <= 69, it flags it as a "Nouvelle Wilaya" (New Province).
*   **Vehicle Type (The "1"):** The first digit of the middle block (`120`) dictates the type via a lookup table (1 = Véhicule Tourisme, 2 = Camion, 9 = Moto).
*   **Registration Year (The "20"):** The last two digits of the middle block. The logic pivots around the year 50. If the value is > 50, it prefixes "19" (e.g., 99 -> 1999). If <= 50, it prefixes "20" (e.g., 20 -> 2020).

---

### 5. Application UI & Dynamic Grouping Engine
*   **Real-time Feed:** The left pane of the dashboard acts as a Socket.IO listener. When a new capture event is emitted, JS creates an HTML node and dynamically prepends it to the list.
*   **Dynamic Client-Side Grouping:** To avoid hitting the SQLite database for sorting queries, the app caches the `capturesData` array in memory. When a user selects a sorting parameter ("Grouper par Wilaya" or "Grouper par Année"), the Javascript engine natively iterates the array, generates new HTML container divs for each category, and appends the relevant captures into them instantly.
