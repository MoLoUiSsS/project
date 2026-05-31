# ParkNet — Smart IoT Parking Management Platform

Plateforme intelligente de gestion de parking avec contrôle d'accès automatisé, reconnaissance de plaques (OCR), caméra smartphone IoT, barrière Arduino et tableau de bord temps réel.

## Fonctionnalités

- 🔍 **OCR intelligent** — Lecture de plaques algériennes via API OCR.space avec preprocessing d'image
- 🚗 **Contrôle de barrière** — Arduino + capteur ultrasonique pour détection automatique
- 📱 **Capture mobile** — Scanner des plaques depuis un smartphone
- 💳 **Gestion des paiements** — Inscription, paiement, et validation automatique
- 📊 **Dashboard temps réel** — SocketIO pour les mises à jour en direct
- 🔐 **Panel Admin** — Gestion des véhicules et journal des accès

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/MoLoUiSsS/project.git
cd project
```

### 2. Installer les dépendances

```bash
pip install flask flask-socketio opencv-python pyserial
```

### 3. Lancer l'application

```bash
python app.py
```

### 4. Ouvrir dans le navigateur

| Page | URL |
|------|-----|
| Dashboard | http://localhost:5000/ |
| Parking Gate | http://localhost:5000/parking |
| Inscription | http://localhost:5000/register |
| Admin | http://localhost:5000/admin |

## Architecture

```
lapi_app/
├── app.py                  # Point d'entrée Flask + SocketIO
├── config.py               # Configuration (OCR, Arduino, DB)
├── database.py             # SQLite setup
├── routes/
│   ├── pages.py            # Routes des pages HTML
│   ├── capture_routes.py   # API upload + captures
│   ├── vehicle_routes.py   # API inscription + paiement
│   ├── parking_routes.py   # API barrière + accès
│   └── arduino_routes.py   # API Arduino serial
├── services/
│   ├── ocr_service.py      # OCR avec preprocessing
│   ├── camera_service.py   # Capture webcam
│   ├── gate_service.py     # Logique d'accès
│   └── arduino_service.py  # Communication série Arduino
├── templates/              # Pages HTML (Jinja2)
├── static/
│   ├── css/                # Styles
│   └── js/                 # Scripts frontend
└── arduino/                # Code Arduino (capteur + servo)
```

## Technologies

- **Backend** : Python, Flask, Flask-SocketIO
- **Frontend** : HTML, CSS, JavaScript, Socket.IO
- **OCR** : OCR.space API + OpenCV preprocessing
- **Base de données** : SQLite
- **Hardware** : Arduino Uno, capteur ultrasonique HC-SR04, servo moteur

## Auteur

Mohammed Hammadi — ESI-SBA
