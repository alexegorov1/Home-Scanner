import shutil
import logging
import os
import time
import json
from datetime import datetime
from core.config_loader import load_config

class DiskMonitor:
    def __init__(self, path="/", log_file=None):
        self.path = os.path.abspath(path)
        self.config = load_config()
        self.threshold_percent = self.config.get("thresholds", {}).get("disk_usage_percent", 85)
        self.min_free_gb = self.config.get("thresholds", {}).get("disk_min_free_gb", 2)
        self.alert_on_mount_failure = self.config.get("alerts", {}).get("disk_mount_failure", True)
        self.snapshot_dir = self.config.get("paths", {}).get("snapshot_dir", "snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self.logger = self._setup_logger(log_file)

    def check_disk_usage(self):
        if not os.path.exists(self.path):
            msg = f"Path does not exist: {self.path}"
            if self.alert_on_mount_failure:
                self.logger.error(msg)
            return [msg]
        try:
            usage = shutil.disk_usage(self.path)
            gb = lambda b: b / 1_073_741_824
            total_gb, used_gb, free_gb = map(gb, (usage.total, usage.used, usage.free))
            percent_used = (usage.used / usage.total) * 100
            alerts = []
            if percent_used >= self.threshold_percent:
                msg = f"Disk usage alert: {percent_used:.2f}% used on {self.path} (limit {self.threshold_percent}%)"
                self.logger.warning(msg)
                alerts.append(msg)
            if free_gb < self.min_free_gb:
                msg = f"Low disk space alert: {free_gb:.2f} GB free on {self.path} (minimum: {self.min_free_gb} GB)"
                self.logger.warning(msg)
                alerts.append(msg)
            self.logger.info(f"Disk OK: {used_gb:.2f} GB used / {total_gb:.2f} GB total / {free_gb:.2f} GB free on {self.path}")
            self._save_snapshot(percent_used, total_gb, used_gb, free_gb)
            return alerts
        except PermissionError as e:
            msg = f"Permission denied accessing {self.path}: {e}"
            self.logger.error(msg)
            return [msg]
        except Exception as e:
            msg = f"Unexpected error while checking disk: {e}"
            self.logger.exception(msg)
            return [msg]

    def export_status(self, output_path):
        try:
            usage = shutil.disk_usage(self.path)
            gb = lambda b: b / 1_073_741_824
            report = {
                "checked_at": datetime.utcnow().isoformat(timespec="seconds"),
                "path": self.path,
                "total_gb": round(gb(usage.total), 2),
                "used_gb": round(gb(usage.used), 2),
                "free_gb": round(gb(usage.free), 2),
                "percent_used": round((usage.used / usage.total) * 100, 2)
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Disk status exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export disk status: {e}")
