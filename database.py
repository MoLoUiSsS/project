import sqlite3
from config import DB_FILE


def get_db_connection():
    try:
        connection = sqlite3.connect(DB_FILE)
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def setup_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id_camera INTEGER PRIMARY KEY AUTOINCREMENT,
            adresse_ip TEXT,
            localisation TEXT,
            statut TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id_capture INTEGER PRIMARY KEY AUTOINCREMENT,
            plaque_immatriculation TEXT,
            date_heure_capture TEXT,
            chemin_image TEXT,
            fiabilite_lecture REAL,
            id_camera INTEGER,
            FOREIGN KEY (id_camera) REFERENCES cameras(id_camera)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            plaque_immatriculation TEXT NOT NULL UNIQUE,
            phone TEXT,
            date_registered TEXT NOT NULL,
            is_paid INTEGER DEFAULT 0,
            payment_date TEXT,
            payment_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'normal'
        )
        """)

        # Migration for existing databases
        try:
            cursor.execute("ALTER TABLE registered_vehicles ADD COLUMN status TEXT DEFAULT 'normal'")
        except sqlite3.OperationalError:
            pass # Column likely already exists

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaque_immatriculation TEXT,
            timestamp TEXT NOT NULL,
            access_granted INTEGER DEFAULT 0,
            reason TEXT,
            chemin_image TEXT,
            distance_cm REAL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            description TEXT,
            timestamp TEXT NOT NULL,
            performed_by TEXT DEFAULT 'admin'
        )
        """)

        cursor.execute("SELECT id_camera FROM cameras WHERE id_camera = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO cameras (id_camera, adresse_ip, localisation, statut) "
                "VALUES (1, 'Appareil Mobile', 'Mode Capture Libre', 'Actif')"
            )

        conn.commit()
        print("  Database: OK (all tables ready)")
    except Exception as e:
        print(f"  Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == '__main__':
    setup_database()
