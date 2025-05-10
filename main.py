import time
import threading
from core.logger import Logger
from core.scanner import NetworkScanner
from core.analysis import LogAnalyzer
from core.alerts import AlertManager
from core.database import IncidentDatabase
from monitoring.process_monitor import ProcessMonitor
from security.file_monitor import FileMonitor
from monitoring.disk_monitor import DiskMonitor
from system.uptime_monitor import UptimeMonitor
from monitoring.user_activity_monitor import UserActivityMonitor
from api.server import run_api_server
from cli.cli import HomescannerCLI


def build_components():
    logger = Logger()
    scanner = NetworkScanner(target="127.0.0.1")
    analyzer = LogAnalyzer()
    alert_manager = AlertManager()
    db = IncidentDatabase()
    process_monitor = ProcessMonitor()
    file_monitor = FileMonitor()
    disk_monitor = DiskMonitor()
    uptime_monitor = UptimeMonitor()
    user_activity_monitor = UserActivityMonitor()

    return {
        "logger": logger,
        "scanner": scanner,
        "analyzer": analyzer,
        "alert_manager": alert_manager,
        "db": db,
        "process_monitor": process_monitor,
        "file_monitor": file_monitor,
        "disk_monitor": disk_monitor,
        "uptime_monitor": uptime_monitor,
        "user_activity_monitor": user_activity_monitor
    }


def main_loop(components):
    logger = components["logger"]
    scanner = components["scanner"]
    analyzer = components["analyzer"]
    alert_manager = components["alert_manager"]
    db = components["db"]
    process_monitor = components["process_monitor"]
    file_monitor = components["file_monitor"]
    disk_monitor = components["disk_monitor"]
    uptime_monitor = components["uptime_monitor"]
    user_activity_monitor = components["user_activity_monitor"]

    logger.log("Homescanner initialized and running.", level="info")

    while True:
        start_time = time.time()
        logger.log("Starting scan cycle...", level="info")

        try:
            threats = scanner.scan()
            for threat in threats:
                message = f"Threat detected: {threat}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="network", severity="warning", source="scanner")

            anomalies = analyzer.analyze_logs()
            for anomaly in anomalies:
                message = f"Log anomaly detected: {anomaly}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="log", severity="warning", source="log_analyzer")

            suspicious_processes = process_monitor.check_processes()
            for proc in suspicious_processes:
                message = f"Suspicious process detected: {proc}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="process", severity="warning", source="process_monitor")

            modified_files = file_monitor.check_files()
            for file in modified_files:
                message = f"Modified file detected: {file}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="filesystem", severity="warning", source="file_monitor")

            disk_warnings = disk_monitor.check_disk_usage()
            for warning in disk_warnings:
                message = f"Disk warning: {warning}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="disk", severity="warning", source="disk_monitor")

            new_logins = user_activity_monitor.check_new_logins()
            for login in new_logins:
                message = f"New user login detected: {login}"
                logger.log(message, level="warning")
                alert_manager.send_alert(message)
                db.add_incident(message, type="account", severity="warning", source="user_monitor")

            uptime_status = uptime_monitor.get_uptime()
            logger.log(uptime_status, level="info")

            logger.log("Scan cycle complete. Sleeping until next cycle...", level="info")
            elapsed = time.time() - start_time
            time.sleep(max(0, 60 - elapsed))

        except Exception as e:
            logger.log(f"Error during scan cycle: {e}", level="error")


def health_check(components):
    logger = components["logger"]
    db = components["db"]
    alert_manager = components["alert_manager"]
    scanner = components["scanner"]
    file_monitor = components["file_monitor"]
    disk_monitor = components["disk_monitor"]

    logger.log("Performing system health check...", level="info")

    try:
        if db.get_connection() is None:
            logger.log("Health Check Failed: Cannot connect to incident database.", level="error")
        else:
            logger.log("Database connection check passed.", level="info")
    except Exception as e:
        logger.log(f"Health Check Error: Database failure - {e}", level="error")

    try:
        test_threats = scanner.scan()
        logger.log(f"Network scan test returned {len(test_threats)} result(s).", level="info")
    except Exception as e:
        logger.log(f"Health Check Error: Scanner failure - {e}", level="error")

    try:
        file_monitor.check_files()
        logger.log("File monitor test ran successfully.", level="info")
    except Exception as e:
        logger.log(f"Health Check Error: File monitor failure - {e}", level="error")

    try:
        disk_monitor.check_disk_usage()
        logger.log("Disk monitor test ran successfully.", level="info")
    except Exception as e:
        logger.log(f"Health Check Error: Disk monitor failure - {e}", level="error")

    if not alert_manager.enabled:
        logger.log("Health Check Warning: Email alerts are disabled or misconfigured.", level="warning")
    else:
        logger.log("AlertManager configuration check passed.", level="info")

    logger.log("Health check completed.", level="info")


def run_all():
    components = build_components()
    cli = HomescannerCLI(
        components["uptime_monitor"],
        components["disk_monitor"],
        components["logger"],
        components["analyzer"],
        components["db"],
        components["file_monitor"],
        components["process_monitor"],
        components["scanner"],
        components["alert_manager"]
    )

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    cli_thread = threading.Thread(target=cli.start, daemon=True)

    api_thread.start()
    cli_thread.start()

    main_loop(components)


if __name__ == "__main__":
    run_all()
