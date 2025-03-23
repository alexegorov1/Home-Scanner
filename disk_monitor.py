import shutil
import logging
import os

class DiskMonitor:
    def __init__(self, path="/"):
        self.path = path
        self.threshold_percent = 85
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def check_disk_usage(self):
        if not os.path.exists(self.path):
            logging.error(f"DiskMonitor: Path does not exist - {self.path}")
            return [f"DiskMonitor error: Path does not exist - {self.path}"]

        if not os.access(self.path, os.R_OK):
            logging.error(f"DiskMonitor: Path is not readable - {self.path}")
            return [f"DiskMonitor error: Path is not readable - {self.path}"]

        try:
            usage = shutil.disk_usage(self.path)
            percent_used = (usage.used / usage.total) * 100
            if percent_used >= self.threshold_percent:
                return [f"Disk usage warning: {percent_used:.2f}% used on {self.path}"]
            return []
        except PermissionError:
            logging.exception(f"DiskMonitor: Permission denied while accessing {self.path}")
            return [f"DiskMonitor error: Permission denied for {self.path}"]
        except FileNotFoundError:
            logging.exception(f"DiskMonitor: Path not found during check - {self.path}")
            return [f"DiskMonitor error: Path not found - {self.path}"]
        except OSError as e:
            logging.exception(f"DiskMonitor: OS error while checking disk usage for {self.path}: {e}")
            return [f"DiskMonitor error: OS error while checking {self.path}"]
        except Exception as e:
            logging.exception(f"DiskMonitor: Unexpected error while checking disk usage for {self.path}: {e}")
            return [f"DiskMonitor error: Unexpected issue with {self.path}"]
