# LAPI Mobile & Dashboard Application

Application LAPI (Lecture Automatisée de Plaques d'Immatriculation) avec interface full-stack. Conçue pour permettre aux opérateurs de prendre une photo via la caméra de leur smartphone (ou télécharger une photo sur ordinateur) et visualiser la remonte des plaques en Temps Réel.

## Fonctionnalités 
- Serveur Flask / Socket.IO interactif
- Base de données MySQL pour stocker les captures
- Front-end avec Glassmorphism et Mode Sombre
- Notification temps-réel avec Socket.io lors d'une capture entrante

## Instructions D'Installation & D'Exécution

### 1) Configuration de la base de données
L'application utilise une base de données MySQL. Assurez-vous d'avoir WAMP, XAMPP, ou un serveur MySQL local d'actif.
- Si vous avez un mot de passe MySQL (par défaut sous XAMPP/WAMP, souvent vide `''` ou `root`), veuillez l'indiquer dans les fichiers :
  - `init_db.py` (Ligne 5, `DB_PASSWORD = ''`)
  - `app.py` (Ligne 19, `DB_PASSWORD = ''`)

Lancez le script d'initialisation pour créer la base et les tables nécessaires :
```bash
python init_db.py
```

### 2) Installation des dépendances
Il faut installer Flask, Socket.IO, et PyMySQL (il est conseillé d'utiliser un environnement virtuel python comme venv, mais vous pouvez aussi les installer globalement).
```bash
pip install -r requirements.txt
```

### 3) Lancement de l'application
Démarrez le serveur Flask en tapant cette commande :
```bash
python app.py
```
Le serveur démarrera sur `http://0.0.0.0:5000` (accessible sur `http://localhost:5000` ou `http://127.0.0.1:5000`).

### Mode Smartphone
Pour utiliser son **smartphone ou tablette comme caméra** :
1. Connectez votre mobile sur le **même réseau WiFi** que votre ordinateur.
2. Trouvez l'adresse IP locale de votre ordinateur (ex: `192.168.x.x` avec la commande `ipconfig` sur l'invite de commande).
3. Sur votre mobile, ouvrez un navigateur web et tapez `http://VOTRE_ADRESSE_IP:5000`
4. Cliquez sur **"Prendre Photo"** dans le menu de gauche : votre smartphone vous proposera directement d'utiliser l'Appareil Photo !
5. Sur l'écran de votre ordinateur (le dashboard), vous verrez la plaque s'ajouter en temps réel.
