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
        server = HTTPServer((self.host, self.port), self._handler())
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def _handler(self):
        exporter = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/metrics":
                    self.send_response(404)
                    self.end_headers()
                    return

                exporter._collect_metrics()

                response = "\n".join([
                    f"# HELP {k} {v['help']}\n# TYPE {k} {v['type']}\n{k} {v['value']}"
                    for k, v in exporter.metrics.items()
                ])

                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))

        return Handler

    def _collect_metrics(self):
        try:
            conn = self.db.get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM incidents")
                count = cur.fetchone()[0]
                self.metrics["homescanner_incidents_total"] = {
                    "help": "Total number of recorded incidents",
                    "type": "counter",
                    "value": count
                }
                cur.execute("SELECT COUNT(*) FROM incidents WHERE severity = 'critical'")
                critical = cur.fetchone()[0]
                self.metrics["homescanner_critical_incidents_total"] = {
                    "help": "Number of critical incidents recorded",
                    "type": "counter",
                    "value": critical
                }
                conn.close()
        except Exception:
            self.metrics["homescanner_incidents_total"] = {
                "help": "Total number of recorded incidents",
                "type": "counter",
                "value": 0
            }

        try:
            disk_status = self.disk_monitor.check_disk_usage()
            disk_alerts = len(disk_status)
            self.metrics["homescanner_disk_alerts_total"] = {
                "help": "Current number of disk space or usage alerts",
                "type": "gauge",
                "value": disk_alerts
            }
        except Exception:
            self.metrics["homescanner_disk_alerts_total"] = {
                "help": "Current number of disk space or usage alerts",
                "type": "gauge",
                "value": 0
            }

        try:
            uptime_str = self.uptime_monitor.get_uptime()
            parts = uptime_str.split()
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
