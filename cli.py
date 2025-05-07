import sys
from time import sleep
from colorama import Fore, Style, init
from system.uptime_monitor import UptimeMonitor
from monitoring.disk_monitor import DiskMonitor
from core.logger import Logger
from core.analysis import LogAnalyzer
from core.database import IncidentDatabase
from security.file_monitor import FileMonitor
from monitoring.process_monitor import ProcessMonitor
from core.scanner import NetworkScanner
from core.alerts import AlertManager

init(autoreset=True)

class HomescannerCLI:
    def __init__(self, uptime_monitor, disk_monitor, logger, analyzer, db, file_monitor, process_monitor, scanner, alert_manager):
        self.uptime_monitor = uptime_monitor
        self.disk_monitor = disk_monitor
        self.logger = logger
        self.analyzer = analyzer
        self.db = db
        self.file_monitor = file_monitor
        self.process_monitor = process_monitor
        self.scanner = scanner
        self.alert_manager = alert_manager
        self.commands = {
            "help": self.help,
            "exit": self.exit,
            "status": self.status,
            "uptime": self.uptime,
            "disk": self.disk,
            "logs": self.logs,
            "incidents": self.incidents,
            "scan": self.manual_scan
        }

    def start(self):
        print(Fore.CYAN + "Homescanner CLI started. Type 'help' for commands.")
        while True:
            try:
                command = input(Fore.YELLOW + "> ").strip().lower()
                (self.commands.get(command) or self.unknown_command)()
            except KeyboardInterrupt:
                self.exit()

    def help(self):
        print(Fore.GREEN + "\nAvailable commands:")
        for cmd in self.commands:
            print(f"  {cmd}")
        print()

    def exit(self):
        print(Fore.CYAN + "Exiting CLI...")
        sleep(1)
        sys.exit(0)

    def status(self):
        print(Fore.GREEN + "System is running. Monitors are active.")

    def uptime(self):
        print(Fore.BLUE + self.uptime_monitor.get_uptime())

    def disk(self):
        warnings = self.disk_monitor.check_disk_usage()
        if warnings:
            for w in warnings:
                print(Fore.RED + w)
        else:
            print(Fore.GREEN + "Disk usage is within normal limits.")

    def logs(self):
        print(Fore.MAGENTA + "\n--- Last 20 Log Entries ---")
        for line in self.logger.read_logs(20):
            print(line.strip())
        print(Fore.MAGENTA + "---------------------------\n")

    def incidents(self):
        conn = self.db.get_connection()
        if not conn:
            print(Fore.RED + "Failed to connect to the database.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, description FROM incidents ORDER BY timestamp DESC LIMIT 5")
            rows = cursor.fetchall()
            if not rows:
                print(Fore.YELLOW + "No incidents found.")
            else:
                print(Fore.MAGENTA + "\n--- Recent Incidents ---")
                for ts, desc in rows:
                    print(f"{ts} | {desc}")
                print(Fore.MAGENTA + "------------------------\n")
        finally:
            conn.close()

    def manual_scan(self):
        print(Fore.CYAN + "Running full scan...")

        for threat in self.scanner.scan():
            self._report_issue("Threat detected", threat)

        for anomaly in self.analyzer.analyze_logs():
            self._report_issue("Log anomaly detected", anomaly)

        for file in self.file_monitor.check_files():
            self._report_issue("Modified file detected", file)

        for proc in self.process_monitor.check_processes():
            self._report_issue("Suspicious process detected", proc)

        for warning in self.disk_monitor.check_disk_usage():
            self._report_issue("Disk warning", warning)

        print(Fore.GREEN + "Scan complete.\n")

    def _report_issue(self, prefix, message):
        entry = f"{prefix}: {message}"
        self.logger.log(entry)
        self.alert_manager.send_alert(message)
        self.db.add_incident(message)
        print(Fore.RED + entry)

    def unknown_command(self):
        print(Fore.RED + "Unknown command. Type 'help' to list available commands.")
