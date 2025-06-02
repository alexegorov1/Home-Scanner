import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock

class IncidentDatabase:
    def __init__(self, db_file=None):
        base_dir = Path(__file__).resolve().parent.parent
        default_path = base_dir / "data" / "incidents.db"
        self.db_file = Path(db_file) if db_file and "PLACEHOLDER_PATH" not in db_file else default_path
        self._lock = Lock()
        self._ensure_directory()
        self._initialize_database()

    def _initialize_database(self):
        try:
            with self._connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        type TEXT DEFAULT 'generic',
                        severity TEXT DEFAULT 'info',
                        description TEXT NOT NULL,
                        source TEXT DEFAULT 'unknown'
                    )
                """)
        except sqlite3.Error as e:
            logging.exception(f"[DB INIT] Schema initialization failed: {e}")
            raise RuntimeError("Failed to initialize database schema")

    def _connect(self):
        return sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)

    def add_incident(self, description, type="generic", severity="info", source="unknown"):
        if not isinstance(description, str) or not description.strip():
            logging.error("[DB INSERT] Invalid incident description")
            return False

        try:
            with self._lock, self._connect() as conn:
                conn.execute("""
                    INSERT INTO incidents (timestamp, type, severity, description, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    type.strip().lower(),
                    severity.strip().lower(),
                    description.strip(),
                    source.strip().lower()
                ))
                logging.info(f"[DB INSERT] Incident recorded: {description}")
                return True
        except sqlite3.Error as e:
            logging.exception(f"[DB INSERT] SQLite error: {e}")
            return False

    def query_incidents(self, limit=50, severity=None, type=None, source=None, since=None):
        try:
            with self._connect() as conn:
                query = "SELECT * FROM incidents"
                conditions = []
                params = []

                if severity:
                    conditions.append("severity = ?")
                    params.append(severity.strip().lower())

                if type:
                    conditions.append("type = ?")
                    params.append(type.strip().lower())

                if source:
                    conditions.append("source = ?")
                    params.append(source.strip().lower())

                if since:
                    conditions.append("timestamp >= ?")
                    params.append(since)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logging.exception(f"[DB QUERY] Failed to fetch incidents: {e}")
            return []

    def count_incidents(self, severity=None):
        try:
            with self._connect() as conn:
                query = "SELECT COUNT(*) FROM incidents"
                params = []

                if severity:
                    query += " WHERE severity = ?"
                    params.append(severity.strip().lower())

                cursor = conn.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.exception(f"[DB COUNT] Failed to count incidents: {e}")
            return 0

    def get_latest_incident(self):
        try:
            with self._connect() as conn:
                cursor = conn.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 1")
                return cursor.fetchone()
        except Exception as e:
            logging.exception(f"[DB FETCH] Failed to fetch latest incident: {e}")
            return None
