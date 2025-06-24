import sys
import asyncio
import json
from argparse import ArgumentParser, Namespace
from core.logger import Logger
from core.analysis import LogAnalyzer
from core.alerts import AlertManager
from core.database import IncidentDatabase
from monitoring.process_monitor import ProcessMonitor
from security.file_monitor import FileMonitor
from monitoring.disk_monitor import DiskMonitor
from system.uptime_monitor import UptimeMonitor
from monitoring.user_activity_monitor import UserActivityMonitor
from core.scanner import NetworkScanner


class HomescannerCLI:
    def __init__(self, args: Namespace):
        self.args = args
        self.logger = Logger()
        self.scanner = NetworkScanner()
        self.analyzer = LogAnalyzer()
        self.alert_manager = AlertManager()
        self.db = IncidentDatabase()
        self.process_monitor = ProcessMonitor()
        self.file_monitor = FileMonitor()
        self.disk_monitor = DiskMonitor()
        self.uptime_monitor = UptimeMonitor()
        self.user_monitor = UserActivityMonitor()

    async def run(self):
        if self.args.command == "status":
            self.print_status()
        elif self.args.command == "uptime":
            self.print_uptime()
        elif self.args.command == "disk":
            self.check_disk()
        elif self.args.command == "logs":
            self.show_logs()
        elif self.args.command == "incidents":
            self.show_incidents()
        elif self.args.command == "scan":
            await self.manual_scan()
        else:
            print("Unknown command.")

    def print_status(self):
        print("System is running. Monitors are active.")

    def print_uptime(self):
        print(self.uptime_monitor.get_uptime())

    def check_disk(self):
        warnings = self.disk_monitor.check_disk_usage()
        if warnings:
            for w in warnings:
                print(w)
        else:
            print("Disk usage is within normal limits.")

    def show_logs(self):
        logs = self.logger.read_logs(lines=self.args.lines)
        if self.args.json:
            print(json.dumps({"logs": logs}, indent=2))
        else:
            for line in logs:
                print(line.strip())

    def show_incidents(self):
        conn = self.db.get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, description FROM incidents ORDER BY timestamp DESC LIMIT ?", (self.args.count,))
            rows = cursor.fetchall()
            if self.args.json:
                print(json.dumps({"incidents": rows}, indent=2))
            else:
                for ts, desc in rows:
                    print(f"{ts} | {desc}")
        finally:
            conn.close()

    async def manual_scan(self):
        results = []

        threats = await self.scanner.scan()
        for threat in threats:
            self._report_issue("Threat detected", threat)
            results.append(threat)

        anomalies = self.analyzer.analyze_logs()
        for anomaly in anomalies:
            self._report_issue("Log anomaly detected", anomaly)
            results.append(anomaly)

        files = self.file_monitor.check_files()
        for f in files:
            self._report_issue("Modified file detected", f)
            results.append(f)

        procs = self.process_monitor.check_processes()
        for p in procs:
            self._report_issue("Suspicious process detected", p)
            results.append(p)

        warnings = self.disk_monitor.check_disk_usage()
        for w in warnings:
            self._report_issue("Disk warning", w)
            results.append(w)

        if self.args.json:
            print(json.dumps({"scan_results": results}, indent=2))

    def _report_issue(self, prefix, message):
        entry = f"{prefix}: {message}"
        self.logger.log(entry)
        self.alert_manager.send_alert(message)
        self.db.add_incident(message)
        if not self.args.json:
            print(entry)


def build_parser():
    parser = ArgumentParser(prog="homescanner")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status")
    subparsers.add_parser("uptime")
    subparsers.add_parser("disk")

    logs_parser = subparsers.add_parser("logs")
    logs_parser.add_argument("--lines", type=int, default=20)
    logs_parser.add_argument("--json", action="store_true")

    inc_parser = subparsers.add_parser("incidents")
    inc_parser.add_argument("--count", type=int, default=5)
    inc_parser.add_argument("--json", action="store_true")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--json", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    cli = HomescannerCLI(args)
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
