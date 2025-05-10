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
    return {
        "logger": logger,
        "scanner": NetworkScanner(target="127.0.0.1"),
        "analyzer": LogAnalyzer(),
        "alert_manager": AlertManager(),
        "db": IncidentDatabase(),
        "process_monitor": ProcessMonitor(),
        "file_monitor": FileMonitor(),
        "disk_monitor": DiskMonitor(),
        "uptime_monitor": UptimeMonitor(),
        "user_activity_monitor": UserActivityMonitor()
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

    try:
        while True:
            start = time.time()
            logger.log("Starting scan cycle...", level="info")

            try:
                for threat in scanner.scan():
                    logger.log(f"Threat detected: {threat}", level="warning")
                    alert_manager.send_alert(threat)
                    db.add_incident(threat, type="network", severity="warning", source="scanner")

                for anomaly in analyzer.analyze_logs():
                    logger.log(f"Log anomaly detected: {anomaly}", level="warning")
                    alert_manager.send_alert(anomaly)
                    db.add_incident(anomaly, type="log", severity="warning", source="log_analyzer")

                for proc in process_monitor.check_processes():
                    logger.log(f"Suspicious process detected: {proc}", level="warning")
                    alert_manager.send_alert(proc)
                    db.add_incident(proc, type="process", severity="warning", source="process_monitor")

                for file in file_monitor.check_files():
                    logger.log(f"Modified file detected: {file}", level="warning")
                    alert_manager.send_alert(file)
                    db.add_incident(file, type="filesystem", severity="warning", source="file_monitor")

                for warning in disk_monitor.check_disk_usage():
                    logger.log(f"Disk warning: {warning}", level="warning")
                    alert_manager.send_alert(warning)
                    db.add_incident(warning, type="disk", severity="warning", source="disk_monitor")

                for login in user_activity_monitor.check_new_logins():
                    msg = f"New user login detected: {login}"
                    logger.log(msg, level="warning")
                    alert_manager.send_alert(msg)
                    db.add_incident(msg, type="account", severity="warning", source="user_monitor")

                logger.log(uptime_monitor.get_uptime(), level="info")
                logger.log("Scan cycle complete. Sleeping...", level="info")
                time.sleep(max(0, 60 - (time.time() - start)))

            except Exception as e:
                logger.log(f"Error during scan cycle: {e}", level="error")

    except KeyboardInterrupt:
        logger.log("Shutdown requested via keyboard interrupt.", level="info")
    except Exception as e:
        logger.log(f"Critical error in main loop: {e}", level="critical")
        raise

def health_check(components):
    logger = components["logger"]
    db = components["db"]
    alert_manager = components["alert_manager"]
    scanner = components["scanner"]
    file_monitor = components["file_monitor"]
    disk_monitor = components["disk_monitor"]

    logger.log("Performing health check...", level="info")

    try:
        if db.get_connection() is None:
            logger.log("Database connection failed.", level="error")
        else:
            logger.log("Database connection OK.", level="info")
    except Exception as e:
        logger.log(f"DB check error: {e}", level="error")

    try:
        logger.log(f"Network scan returned {len(scanner.scan())} result(s).", level="info")
    except Exception as e:
        logger.log(f"Scanner error: {e}", level="error")

    try:
        file_monitor.check_files()
        logger.log("File monitor check passed.", level="info")
    except Exception as e:
        logger.log(f"File monitor error: {e}", level="error")

    try:
        disk_monitor.check_disk_usage()
        logger.log("Disk monitor check passed.", level="info")
    except Exception as e:
        logger.log(f"Disk monitor error: {e}", level="error")

    if not alert_manager.enabled:
        logger.log("Email alerts disabled or misconfigured.", level="warning")
    else:
        logger.log("AlertManager config OK.", level="info")

    logger.log("Health check complete.", level="info")

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
    threading.Thread(target=run_api_server, daemon=True).start()
    threading.Thread(target=cli.start, daemon=True).start()
    main_loop(components)
