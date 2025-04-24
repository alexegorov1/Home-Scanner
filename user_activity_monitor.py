import logging
import platform
from datetime import datetime
from typing import List, Set, Optional, Dict

if platform.system() == "Windows":
    import subprocess
else:
    import psutil


class UserActivityMonitor:
    def __init__(self, track_history: bool = False):
        self.logger = self._init_logger()
        self._platform = platform.system()
        self._track_history = track_history
        self.known_users: Set[str] = set()
        self.login_history: List[Dict[str, str]] = []
        self._initialize()

    def _init_logger(self) -> logging.Logger:
        logger = logging.getLogger("UserActivityMonitor")
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize(self):
        """Capture current users on startup to avoid false positives."""
        users = self._fetch_logged_in_users()
        self.known_users = set(users) if users else set()

    def _fetch_logged_in_users(self) -> List[str]:
        try:
            if self._platform == "Windows":
                output = subprocess.check_output("query user", shell=True).decode("utf-8", errors="ignore")
                lines = output.strip().splitlines()[1:]  # Skip header
                return [line.split()[0] for line in lines if line.strip()]
            else:
                return [user.name for user in psutil.users()]
        except Exception as e:
            self.logger.error(f"Failed to retrieve logged-in users: {e}")
            return []

    def check_new_logins(self) -> List[str]:
        users = self._fetch_logged_in_users()
        if not users:
            return []

        current_users = set(users)
        new_logins = sorted(current_users - self.known_users)

        if new_logins:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for user in new_logins:
                self.logger.warning(f"New login detected: {user} at {now}")
                if self._track_history:
                    self.login_history.append({
                        "user": user,
                        "timestamp": now,
                        "platform": self._platform
                    })

        self.known_users = current_users
        return new_logins

    def get_login_history(self) -> Optional[List[Dict[str, str]]]:
        return self.login_history if self._track_history else None
