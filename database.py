import sqlite3
import os

class IncidentDatabase:
    def __init__(self, db_file="data/incidents.db"):
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    description TEXT
                )
            """)
            conn.commit()

    def add_incident(self, description):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO incidents (timestamp, description) VALUES (datetime('now'), ?)", (description,))
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_file)
