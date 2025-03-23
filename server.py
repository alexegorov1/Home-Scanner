from flask import Flask, jsonify
from core.database import IncidentDatabase
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

# Placeholder for database path
DB_PATH = "PLACEHOLDER_PATH/incidents.db"
db = IncidentDatabase(db_file=DB_PATH)

@app.route("/incidents", methods=["GET"])
def get_incidents():
    conn = None
    try:
        conn = db.get_connection()
        if conn is None:
            logging.error("Database connection returned None")
            return jsonify({"error": "Could not connect to database"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        return jsonify(data), 200

    except sqlite3.OperationalError as e:
        logging.exception(f"SQLite operational error: {e}")
        return jsonify({"error": "Database operation failed"}), 500

    except sqlite3.DatabaseError as e:
        logging.exception(f"SQLite database error: {e}")
        return jsonify({"error": "Internal database error"}), 500

    except Exception as e:
        logging.exception(f"Unexpected error while retrieving incidents: {e}")
        return jsonify({"error": "Unexpected server error"}), 500

    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logging.warning(f"Error closing database connection: {e}")

def run_api_server(host="PLACEHOLDER_HOST", port=PLACEHOLDER_PORT, debug=False):
    try:
        logging.info(f"Starting API server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except OSError as e:
        logging.exception(f"Port binding failed or server error: {e}")
    except Exception as e:
        logging.exception(f"Unhandled exception in API server: {e}")

if __name__ == "__main__":
    run_api_server()
