import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from core.database import IncidentDatabase
from monitoring.disk_monitor import DiskMonitor
from system.uptime_monitor import UptimeMonitor


class MetricsExporter:
    def __init__(self, host='0.0.0.0', port=9100):
        self.host = host
        self.port = port
        self.db = IncidentDatabase()
        self.disk_monitor = DiskMonitor()
        self.uptime_monitor = UptimeMonitor()
        self.metrics = {}

    def start(self):
        server = HTTPServer((self.host, self.port), self._build_handler())
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def _build_handler(self):
        exporter = self

        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/metrics":
                    self.send_error(404, "Not Found")
                    return

                exporter._collect_metrics()
                output = []
                for name, data in exporter.metrics.items():
                    output.append(f"# HELP {name} {data['help']}")
                    output.append(f"# TYPE {name} {data['type']}")
                    output.append(f"{name} {data['value']}")

                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.end_headers()
                self.wfile.write("\n".join(output).encode("utf-8"))

        return MetricsHandler

    def _collect_metrics(self):
        self._metric_incidents()
        self._metric_disk()
        self._metric_uptime()

    def _metric_incidents(self):
        try:
            conn = self.db.get_connection()
            if not conn:
                raise RuntimeError("Database unavailable")

            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM incidents")
            self.metrics["homescanner_incidents_total"] = {
                "help": "Total number of recorded incidents",
                "type": "counter",
                "value": cur.fetchone()[0]
            }

            cur.execute("SELECT COUNT(*) FROM incidents WHERE severity = 'critical'")
            self.metrics["homescanner_critical_incidents_total"] = {
                "help": "Number of critical incidents recorded",
                "type": "counter",
                "value": cur.fetchone()[0]
            }

            conn.close()
        except Exception:
            self.metrics["homescanner_incidents_total"] = {
                "help": "Total number of recorded incidents",
                "type": "counter",
                "value": 0
            }
            self.metrics["homescanner_critical_incidents_total"] = {
                "help": "Number of critical incidents recorded",
                "type": "counter",
                "value": 0
            }

    def _metric_disk(self):
        try:
            alerts = len(self.disk_monitor.check_disk_usage())
            self.metrics["homescanner_disk_alerts_total"] = {
                "help": "Current number of disk space or usage alerts",
                "type": "gauge",
                "value": alerts
            }
        except Exception:
            self.metrics["homescanner_disk_alerts_total"] = {
                "help": "Current number of disk space or usage alerts",
                "type": "gauge",
                "value": 0
            }

    def _metric_uptime(self):
        try:
            parts = self.uptime_monitor.get_uptime().split()
            hours = int(parts[0]) * 24 + int(parts[2])
            self.metrics["homescanner_uptime_hours"] = {
                "help": "System uptime in hours",
                "type": "gauge",
                "value": hours
            }
        except Exception:
            self.metrics["homescanner_uptime_hours"] = {
                "help": "System uptime in hours",
                "type": "gauge",
                "value": 0
            }
