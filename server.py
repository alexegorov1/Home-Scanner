from flask import Flask, jsonify, request
from flask_cors import CORS
from core.database import IncidentDatabase
import logging
import sqlite3

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask app
app = Flask(__name__)
CORS(app)

# Placeholder path — обязательно замени на реальный путь
DB_PATH = "PLACEHOLDER_PATH/incidents.db"
db = IncidentDatabase(db_file=DB_PATH)

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    try:
        conn = db.get_connection()
        if conn:
            conn.execute("SELECT 1")
            conn.close()
            return jsonify({"status": "ok"}), 200
        return jsonify({"status": "error", "message": "No DB connection"}), 500
    except Exception as e:
        logging.exception("Health check failed")
        return jsonify({"status": "error", "message": str(e)}), 500

# GET all incidents
@app.route("/incidents", methods=["GET"])
def get_incidents():
    conn = None
    try:
        conn = db.get_connection()
        if conn is None:
            return jsonify({"error": "Failed to connect to database"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        return jsonify(data), 200
    except Exception as e:
        logging.exception("Error retrieving incidents")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                logging.warning("Failed to close DB connection")

# GET latest incident
@app.route("/incidents/latest", methods=["GET"])
def get_latest_incident():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return jsonify({"message": "No incidents found"}), 404

        columns = [desc[0] for desc in cursor.description]
        return jsonify(dict(zip(columns, row))), 200
    except Exception as e:
        logging.exception("Error retrieving latest incident")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

# POST new incident
@app.route("/incidents", methods=["POST"])
def post_incident():
    try:
        payload = request.get_json()
        if not payload or "description" not in payload:
            return jsonify({"error": "Missing 'description' in request body"}), 400

        description = str(payload["description"]).strip()
        if not description:
            return jsonify({"error": "Description must not be empty"}), 400

        db.add_incident(description)
        logging.info(f"New incident added via API: {description}")
        return jsonify({"message": "Incident recorded"}), 201

    except Exception as e:
        logging.exception("Error while posting new incident")
        return jsonify({"error": "Internal server error"}), 500

# GET incident stats
@app.route("/incidents/stats", methods=["GET"])
def get_incident_stats():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM incidents")
        count = cursor.fetchone()[0]

        cursor.execute("SELECT timestamp FROM incidents ORDER BY timestamp DESC LIMIT 1")
        latest = cursor.fetchone()
        latest_time = latest[0] if latest else "N/A"

        return jsonify({
            "total_incidents": count,
            "latest_incident_time": latest_time
        }), 200
    except Exception as e:
        logging.exception("Error retrieving incident stats")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()

# Server runner
def run_api_server(host="127.0.0.1", port=8080, debug=False):
    try:
        logging.info(f"Starting API server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logging.exception("API server failed to start")

if __name__ == "__main__":
    run_api_server()
