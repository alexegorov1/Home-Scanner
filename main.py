import time
from core.logger import Logger
from core.scanner import NetworkScanner
from core.analysis import LogAnalyzer
from core.alerts import AlertManager
from core.database import IncidentDatabase
from monitoring.process_monitor import ProcessMonitor
from security.file_monitor import FileMonitor
from monitoring.disk_monitor import DiskMonitor
from system.uptime_monitor import UptimeMonitor
from api.server import run_api_server
from cli.cli import start_cli

def main():
    logger = Logger()
    scanner = NetworkScanner(target="127.0.0.1")
    analyzer = LogAnalyzer()
    alert_manager = AlertManager(recipient="admin", smtp_user="placeholder@example.com", smtp_password="placeholder")
    db = IncidentDatabase()
    process_monitor = ProcessMonitor()
    file_monitor = FileMonitor()
    disk_monitor = DiskMonitor()
    uptime_monitor = UptimeMonitor()

    logger.log("Homescanner: System initializing...")

    while True:
        logger.log("Running network scan...")
        threats = scanner.scan()
        for threat in threats:
            logger.log(f"Threat detected: {threat}")
            alert_manager.send_alert(threat)
            db.add_incident(threat)

        logger.log("Analyzing logs for anomalies...")
        anomalies = analyzer.analyze_logs()
        for anomaly in anomalies:
            logger.log(f"Log anomaly detected: {anomaly}")
            alert_manager.send_alert(anomaly)
            db.add_incident(anomaly)

        logger.log("Checking running processes...")
        suspicious_processes = process_monitor.check_processes()
        for proc in suspicious_processes:
            logger.log(f"Suspicious process detected: {proc}")
            alert_manager.send_alert(proc)
            db.add_incident(proc)

        logger.log("Scanning files for suspicious modifications...")
        modified_files = file_monitor.check_files()
        for file in modified_files:
            logger.log(f"Modified file detected: {file}")
            alert_manager.send_alert(file)
            db.add_incident(file)

        logger.log("Checking disk usage...")
        disk_warnings = disk_monitor.check_disk_usage()
        for warning in disk_warnings:
            logger.log(warning)
            alert_manager.send_alert(warning)
            db.add_incident(warning)

        logger.log(uptime_monitor.get_uptime())
        logger.log("Sleeping for next scan cycle...")
        time.sleep(60)

if __name__ == "__main__":
    run_api_server()
    start_cli()
    main()
