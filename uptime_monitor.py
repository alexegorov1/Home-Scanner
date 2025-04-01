import time
from datetime import timedelta, datetime
import logging

class UptimeMonitor:
    def __init__(self):
        self.boot_time = time.monotonic()
        self.wall_start = datetime.utcnow()
        self.logger = logging.getLogger("UptimeMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_uptime(self, raw=False):
        elapsed = timedelta(seconds=time.monotonic() - self.boot_time)
        total_seconds = int(elapsed.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if raw:
            return total_seconds

        segments = []
        if days:
            segments.append(f"{days}d")
        if hours or days:
            segments.append(f"{hours}h")
        if minutes or hours or days:
            segments.append(f"{minutes}m")
        segments.append(f"{seconds}s")

        return f"System uptime: {' '.join(segments)}"

    def get_start_time(self):
        return self.wall_start.strftime("%Y-%m-%d %H:%M:%S UTC")

    def report(self):
        uptime = self.get_uptime()
        start_time = self.get_start_time()
        self.logger.info(f"{uptime} (since {start_time})")
        return f"{uptime} (since {start_time})"
