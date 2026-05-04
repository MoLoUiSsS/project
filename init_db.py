"""
init_db.py — Backward-compatible database initialization script.
Delegates to database.py.
"""

from database import setup_database

if __name__ == '__main__':
    setup_database()
