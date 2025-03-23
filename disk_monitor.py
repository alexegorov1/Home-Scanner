import shutil

class DiskMonitor:
    def __init__(self, path="/"):
        self.path = path
        self.threshold_percent = 85

    def check_disk_usage(self):
        usage = shutil.disk_usage(self.path)
        percent_used = (usage.used / usage.total) * 100
        if percent_used >= self.threshold_percent:
            return [f"Disk usage warning: {percent_used:.2f}% used on {self.path}"]
        return []
