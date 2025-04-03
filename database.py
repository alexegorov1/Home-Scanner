import sqlite3
import os
import logging
from datetime import datetime
import pathlib

class IncidentDatabase:
    def __init__(self, db_file=None):
        if not db_file or "PLACEHOLDER_PATH" in db_file:
            base_dir = pathlib.Path(__file__).resolve().parent.parent
            db_file = os.path.join(base_dir, "data", "incidents.db")
        self.db_file = db_file
        self._ensure_directory()
        self._initialize_database()

    def _ensure_directory(self):
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        except Exception as e:
            logging.exception(f"[DB INIT] Failed to create directory: {e}")
            raise RuntimeError("Could not create directory for database")

    def _initialize_database(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        type TEXT DEFAULT 'generic',
                        severity TEXT DEFAULT 'info',
                        description TEXT NOT NULL,
                        source TEXT DEFAULT 'unknown'
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logging.exception(f"[DB INIT] Schema initialization failed: {e}")
            raise RuntimeError("Failed to initialize database schema")

    def add_incident(self, description, type="generic", severity="info", source="unknown"):
        if not description or not isinstance(description, str):
            logging.error("[DB INSERT] Invalid incident description")
            return
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO incidents (timestamp, type, severity, description, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    type.strip().lower(),
                    severity.strip().lower(),
                    description.strip(),
                    source.strip().lower()
                ))
                conn.commit()
                logging.info(f"[DB INSERT] Incident recorded: {description}")
        except sqlite3.OperationalError as e:
            logging.exception(f"[DB INSERT] Operational error: {e}")
        except sqlite3.IntegrityError as e:
            logging.exception(f"[DB INSERT] Integrity error: {e}")
        except Exception as e:
            logging.exception(f"[DB INSERT] Unexpected error: {e}")

    def query_incidents(self, limit=50, severity=None, type=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                base_query = "SELECT * FROM incidents"
                clauses = []
                params = []

                if severity:
                    clauses.append("severity = ?")
                    params.append(severity.strip().lower())

                if type:
                    clauses.append("type = ?")
                    params.append(type.strip().lower())

                if clauses:
                    base_query += " WHERE " + " AND ".join(clauses)

                base_query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(base_query, params)
                return cursor.fetchall()
        except Exception as e:
            logging.exception(f"[DB QUERY] Failed to fetch incidents: {e}")
            return []

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_file)
        except sqlite3.Error as e:
            logging.exception(f"[DB CONNECT] Failed to connect: {e}")
            return None
