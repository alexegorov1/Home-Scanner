import shutil
import logging
import os
from core.config_loader import load_config

class DiskMonitor:
    def __init__(self, path="/"):
        self.path = path
        cfg = load_config()
        self.threshold_percent = cfg.get("thresholds", {}).get("disk_usage_percent", 85)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def check_disk_usage(self):
        if not os.path.exists(self.path):
            return [f"DiskMonitor: Path does not exist - {self.path}"]

        try:
            usage = shutil.disk_usage(self.path)
            percent_used = (usage.used / usage.total) * 100
            if percent_used >= self.threshold_percent:
                return [f"Disk usage warning: {percent_used:.2f}% used on {self.path}"]
            return []
        except Exception as e:
            logging.exception("DiskMonitor: Unexpected error")
            return [f"DiskMonitor error: {str(e)}"]
