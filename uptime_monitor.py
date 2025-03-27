import time
from datetime import timedelta

class UptimeMonitor:
    def __init__(self):
        self.start_time = time.monotonic()

    def get_uptime(self):
        elapsed = timedelta(seconds=time.monotonic() - self.start_time)
        total_seconds = int(elapsed.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours or days:
            parts.append(f"{hours}h")
        if minutes or hours or days:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return f"System uptime: {' '.join(parts)}"
