import time
import logging
import platform
import json
from datetime import timedelta, datetime
from threading import Lock
from pathlib import Path
from typing import Optional, Union


class UptimeMonitor:
    def __init__(
        self,
        log_file: Optional[Union[str, Path]] = None,
        snapshot_dir: Union[str, Path] = "snapshots/uptime",
        hostname_override: Optional[str] = None,
    ):
        self._boot_time_monotonic = time.monotonic()
        self._wall_start = datetime.utcnow()
        self._hostname = hostname_override or platform.node()
        self._snapshot_dir = Path(snapshot_dir)
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._logger = self._setup_logger(log_file)
        self._lock = Lock()

    def _setup_logger(self, log_file: Optional[Union[str, Path]]) -> logging.Logger:
        logger = logging.getLogger(f"UptimeMonitor:{self._hostname}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler(log_file, encoding="utf-8") if log_file else logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def get_uptime(self, raw: bool = False) -> Union[int, str]:
        with self._lock:
            elapsed = timedelta(seconds=time.monotonic() - self._boot_time_monotonic)
        return int(elapsed.total_seconds()) if raw else self._format_duration(elapsed)

    def _format_duration(self, delta: timedelta) -> str:
        total_seconds = int(delta.total_seconds())
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)

        parts = []
        if days: parts.append(f"{days}d")
        if hours or days: parts.append(f"{hours}h")
        if minutes or hours or days: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    def get_start_time(self, iso: bool = False) -> str:
        return self._wall_start.isoformat(timespec="seconds") + "Z" if iso else self._wall_start.strftime("%Y-%m-%d %H:%M:%S UTC")

    def report(self, include_host: bool = True, log: bool = True) -> str:
        uptime = self.get_uptime()
        start = self.get_start_time()
        prefix = f"[{self._hostname}] " if include_host else ""
        report = f"{prefix}System uptime: {uptime} (since {start})"
        if log:
            self._logger.info(report)
        return report

    def export_status(self, output_path: Optional[Union[str, Path]] = None) -> bool:
        status = {
            "hostname": self._hostname,
            "uptime_seconds": self.get_uptime(raw=True),
            "uptime_text": self.get_uptime(),
            "boot_time": self.get_start_time(iso=True),
            "exported_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
        }
        try:
            path = Path(output_path) if output_path else self._snapshot_dir / f"{int(time.time())}_uptime.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
            self._logger.info(f"Uptime status exported to {path}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to export uptime status: {e}")
            return False

    def is_uptime_exceeding(self, threshold_seconds: int) -> bool:
        try:
            current = self.get_uptime(raw=True)
            return current > threshold_seconds
        except Exception as e:
            self._logger.warning(f"Uptime check failed: {e}")
            return False

    def time_since(self, timestamp_str: str) -> Optional[str]:
        try:
            past = datetime.fromisoformat(timestamp_str.replace("Z", ""))
            delta = datetime.utcnow() - past
            return self._format_duration(delta)
        except Exception as e:
            self._logger.error(f"Invalid timestamp for delta: {timestamp_str} — {e}")
            return None

    def to_dict(self) -> dict:
        return {
            "hostname": self._hostname,
            "uptime_seconds": self.get_uptime(raw=True),
            "uptime_text": self.get_uptime(),
            "boot_time": self.get_start_time(iso=True),
            "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
        }

    def to_json(self) -> str:
        try:
            return json.dumps(self.to_dict(), indent=2)
        except Exception as e:
            self._logger.warning(f"Failed to convert uptime to JSON: {e}")
            return "{}"
