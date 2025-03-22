import time

class UptimeMonitor:
    def __init__(self):
        self.start_time = time.time()

    def get_uptime(self):
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"System uptime: {hours}h {minutes}m {seconds}s"
