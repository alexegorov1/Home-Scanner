from flask import Flask, jsonify
from core.database import IncidentDatabase

app = Flask(__name__)
db = IncidentDatabase()

@app.route('/incidents', methods=['GET'])
def get_incidents():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        incidents = cursor.fetchall()
    return jsonify(incidents)

def run_api_server():
    app.run(port=5000)
