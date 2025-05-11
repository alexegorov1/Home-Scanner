import time
import hashlib
from collections import deque, defaultdict
from datetime import datetime, timedelta

class CorrelationEngine:
    def __init__(self, time_window_sec=120):
        self.time_window = timedelta(seconds=time_window_sec)
        self.events = deque()
        self.correlated_alerts = []
        self.patterns = [
            self._pattern_ransomware_like_behavior,
            self._pattern_post_login_file_activity
        ]

    def _now(self):
        return datetime.utcnow()

    def _hash_event(self, event):
        base = f"{event['type']}|{event['source']}|{event['message']}"
        return hashlib.sha256(base.encode()).hexdigest()

    def ingest_event(self, event):
        timestamp = event.get("timestamp")
        if not isinstance(timestamp, datetime):
            timestamp = self._now()
        event["timestamp"] = timestamp

        self.events.append(event)
        self._expire_old_events()
        self._check_patterns()

    def _expire_old_events(self):
        cutoff = self._now() - self.time_window
        while self.events and self.events[0]["timestamp"] < cutoff:
            self.events.popleft()

    def _check_patterns(self):
        for pattern_func in self.patterns:
            result = pattern_func()
            if result:
                self.correlated_alerts.append(result)

    def get_correlations(self):
        output = self.correlated_alerts[:]
        self.correlated_alerts.clear()
        return output

    def _pattern_ransomware_like_behavior(self):
        proc_events = [e for e in self.events if e["type"] == "process"]
        disk_events = [e for e in self.events if e["type"] == "disk"]
        file_events = [e for e in self.events if e["type"] == "filesystem"]

        if not proc_events or not file_events or not disk_events:
            return None

        proc_hashes = {self._hash_event(e) for e in proc_events}
        file_hashes = {self._hash_event(e) for e in file_events}
        disk_hashes = {self._hash_event(e) for e in disk_events}

        overlap = len(proc_hashes & file_hashes) > 0 and len(disk_hashes) > 0

        if overlap:
            return {
                "timestamp": self._now().isoformat(timespec="seconds"),
                "pattern": "ransomware_like_behavior",
                "description": "Process execution followed by file modification and disk usage spike detected",
                "severity": "critical"
            }

        return None

    def _pattern_post_login_file_activity(self):
        login_events = [e for e in self.events if e["type"] == "account"]
        file_events = [e for e in self.events if e["type"] == "filesystem"]

        if not login_events or not file_events:
            return None

        last_login = max(e["timestamp"] for e in login_events)
        recent_files = [e for e in file_events if e["timestamp"] > last_login]

        if recent_files:
            return {
                "timestamp": self._now().isoformat(timespec="seconds"),
                "pattern": "post_login_file_activity",
                "description": f"Detected {len(recent_files)} file change(s) shortly after user login",
                "severity": "medium"
            }

        return None
