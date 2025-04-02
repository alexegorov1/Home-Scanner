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

    logger.log("Homescanner: System initializing...", level="info")
    logger.log("Homescanner: System is up and running.", level="info")

    try:
        while True:
            cycle_start = time.time()
            logger.log("Starting scan cycle...", level="info")

            try:
                logger.log("Running network scan...", level="info")
                threats = scanner.scan()
                for threat in threats:
                    logger.log(f"Threat detected: {threat}", level="warning")
                    alert_manager.send_alert(threat)
                    db.add_incident(threat, type="network", severity="warning", source="scanner")

                logger.log("Analyzing logs for anomalies...", level="info")
                anomalies = analyzer.analyze_logs()
                for anomaly in anomalies:
                    logger.log(f"Log anomaly detected: {anomaly}", level="warning")
                    alert_manager.send_alert(anomaly)
                    db.add_incident(anomaly, type="log", severity="warning", source="log_analyzer")

                logger.log("Checking running processes...", level="info")
                suspicious_processes = process_monitor.check_processes()
                for proc in suspicious_processes:
                    logger.log(f"Suspicious process detected: {proc}", level="warning")
                    alert_manager.send_alert(proc)
                    db.add_incident(proc, type="process", severity="warning", source="process_monitor")

                logger.log("Scanning files for suspicious modifications...", level="info")
                modified_files = file_monitor.check_files()
                for file in modified_files:
                    logger.log(f"Modified file detected: {file}", level="warning")
                    alert_manager.send_alert(file)
                    db.add_incident(file, type="filesystem", severity="warning", source="file_monitor")

                logger.log("Checking disk usage...", level="info")
                disk_warnings = disk_monitor.check_disk_usage()
                for warning in disk_warnings:
                    logger.log(f"Disk warning: {warning}", level="warning")
                    alert_manager.send_alert(warning)
                    db.add_incident(warning, type="disk", severity="warning", source="disk_monitor")

                logger.log("Checking user sessions...", level="info")
                new_logins = user_activity_monitor.check_new_logins()
                for login in new_logins:
                    logger.log(f"New user login detected: {login}", level="warning")
                    alert_manager.send_alert(f"New user login detected: {login}")
                    db.add_incident(f"New user login detected: {login}", type="account", severity="warning", source="user_monitor")

                uptime = uptime_monitor.get_uptime()
                logger.log(f"{uptime}", level="info")

                logger.log("Scan cycle complete. Sleeping...", level="info")
                elapsed = time.time() - cycle_start
                sleep_time = max(0, 60 - elapsed)
                time.sleep(sleep_time)

            except Exception as scan_error:
                logger.log(f"Error during scan cycle: {scan_error}", level="error")

    except KeyboardInterrupt:
        logger.log("Homescanner: Shutdown requested via keyboard interrupt.", level="info")
    except Exception as fatal_error:
        logger.log(f"Homescanner: Critical error in main loop: {fatal_error}", level="critical")
        raise

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
        tmp_file_check = file_monitor.check_files()
        logger.log(f"File monitor test ran successfully.", level="info")
    except Exception as e:
        logger.log(f"Health Check Error: File monitor failure - {e}", level="error")

    try:
        test_disk = disk_monitor.check_disk_usage()
        logger.log(f"Disk monitor test ran successfully.", level="info")
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
