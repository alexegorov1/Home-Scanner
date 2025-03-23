import sqlite3
import os
import logging

class IncidentDatabase:
    def __init__(self, db_file="PLACEHOLDER_PATH/incidents.db"):
        self.db_file = db_file
        self._ensure_directory()
        self._initialize_database()

    def _ensure_directory(self):
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        except Exception as e:
            logging.exception(f"Failed to create directory for incident database: {e}")
            raise RuntimeError("Failed to create directory for database")

    def _initialize_database(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        description TEXT NOT NULL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logging.exception(f"Failed to initialize the database schema: {e}")
            raise RuntimeError("Database initialization failed")

    def add_incident(self, description):
        if not description or not isinstance(description, str):
            logging.error("Attempted to add invalid incident description to the database")
            return
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO incidents (timestamp, description) VALUES (datetime('now'), ?)",
                    (description.strip(),)
                )
                conn.commit()
        except sqlite3.OperationalError as e:
            logging.exception(f"Database write error (Operational): {e}")
        except sqlite3.IntegrityError as e:
            logging.exception(f"Database write error (Integrity): {e}")
        except Exception as e:
            logging.exception(f"Unexpected error while adding incident: {e}")

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_file)
        except sqlite3.Error as e:
            logging.exception(f"Failed to open database connection: {e}")
            return None
