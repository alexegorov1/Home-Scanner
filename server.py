from flask import Flask, jsonify
from core.database import IncidentDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
db = IncidentDatabase()

@app.route('/incidents', methods=['GET'])
def get_incidents():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
            incidents = cursor.fetchall()
            
            # Convert data into a list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            incidents = [dict(zip(columns, row)) for row in incidents]
        
        return jsonify(incidents), 200
    except Exception as e:
        logging.error(f"Error retrieving incidents: {e}")
        return jsonify({"error": "Failed to retrieve incident data"}), 500

def run_api_server(host='0.0.0.0', port=5000, debug=False):
    logging.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_api_server()
