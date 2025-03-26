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
    def __init__(self,
                 uptime_monitor: UptimeMonitor,
                 disk_monitor: DiskMonitor,
                 logger: Logger,
                 analyzer: LogAnalyzer,
                 db: IncidentDatabase,
                 file_monitor: FileMonitor,
                 process_monitor: ProcessMonitor,
                 scanner: NetworkScanner,
                 alert_manager: AlertManager):
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
                if command in self.commands:
                    self.commands[command]()
                else:
                    print(Fore.RED + "Unknown command. Type 'help' to list available commands.")
            except KeyboardInterrupt:
                self.exit()

    def help(self):
        print(Fore.GREEN + "\nAvailable commands:")
        print("  status     - Show current system status")
        print("  uptime     - Display system uptime")
        print("  disk       - Check disk usage")
        print("  logs       - Show last 20 log entries")
        print("  incidents  - Show latest 5 incidents from database")
        print("  scan       - Manually trigger all scans")
        print("  exit       - Exit the CLI\n")

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
        logs = self.logger.read_logs(lines=20)
        print(Fore.MAGENTA + "\n--- Last 20 Log Entries ---")
        for line in logs:
            print(line.strip())
        print(Fore.MAGENTA + "---------------------------\n")

    def incidents(self):
        conn = self.db.get_connection()
        if conn:
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
            conn.close()
        else:
            print(Fore.RED + "Failed to connect to the database.")

    def manual_scan(self):
        print(Fore.CYAN + "Running full scan...")

        # Network scan
        threats = self.scanner.scan()
        for threat in threats:
            self.logger.log(f"Threat detected: {threat}")
            self.alert_manager.send_alert(threat)
            self.db.add_incident(threat)
            print(Fore.RED + f"Network threat: {threat}")

        # Log analysis
        anomalies = self.analyzer.analyze_logs()
        for anomaly in anomalies:
            self.logger.log(f"Log anomaly detected: {anomaly}")
            self.alert_manager.send_alert(anomaly)
            self.db.add_incident(anomaly)
            print(Fore.RED + f"Log anomaly: {anomaly}")

        # File modifications
        modified_files = self.file_monitor.check_files()
        for file in modified_files:
            self.logger.log(f"Modified file detected: {file}")
            self.alert_manager.send_alert(file)
            self.db.add_incident(file)
            print(Fore.RED + f"File modified: {file}")

        # Process check
        suspicious_processes = self.process_monitor.check_processes()
        for proc in suspicious_processes:
            self.logger.log(f"Suspicious process detected: {proc}")
            self.alert_manager.send_alert(proc)
            self.db.add_incident(proc)
            print(Fore.RED + f"Suspicious process: {proc}")

        # Disk usage
        disk_warnings = self.disk_monitor.check_disk_usage()
        for warning in disk_warnings:
            self.logger.log(warning)
            self.alert_manager.send_alert(warning)
            self.db.add_incident(warning)
            print(Fore.RED + f"Disk warning: {warning}")

        print(Fore.GREEN + "Scan complete.\n")
