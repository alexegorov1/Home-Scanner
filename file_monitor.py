import shutil
import logging
import os
from datetime import datetime
from core.config_loader import load_config

class DiskMonitor:
    def __init__(self, path="/"):
        self.path = path
        self.config = load_config()
        self.threshold_percent = self.config.get("thresholds", {}).get("disk_usage_percent", 85)
        self.min_free_gb = self.config.get("thresholds", {}).get("disk_min_free_gb", 2)
        self.alert_on_mount_failure = self.config.get("alerts", {}).get("disk_mount_failure", True)
        self.logger = logging.getLogger("DiskMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def check_disk_usage(self):
        if not os.path.exists(self.path):
            message = f"DiskMonitor: Path does not exist - {self.path}"
            self.logger.error(message)
            return [message]

        try:
            usage = shutil.disk_usage(self.path)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            percent_used = (usage.used / usage.total) * 100

            alerts = []

            if percent_used >= self.threshold_percent:
                warning = f"Disk usage exceeds threshold: {percent_used:.2f}% used on {self.path} (limit {self.threshold_percent}%)"
                self.logger.warning(warning)
                alerts.append(warning)

            if free_gb < self.min_free_gb:
                warning = f"Low disk space: only {free_gb:.2f} GB free on {self.path} (min required: {self.min_free_gb} GB)"
                self.logger.warning(warning)
                alerts.append(warning)

            self.logger.info(f"Disk check: {used_gb:.2f} GB used / {total_gb:.2f} GB total on {self.path}")

            return alerts

        except PermissionError as e:
            message = f"DiskMonitor: Permission denied while accessing {self.path} - {e}"
            self.logger.error(message)
            return [message]
        except Exception as e:
            message = f"DiskMonitor: Unexpected error - {str(e)}"
            self.logger.exception(message)
            return [message]
