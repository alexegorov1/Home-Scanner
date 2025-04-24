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
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize(self):
        """Initial snapshot of current users to avoid false positives on start."""
        try:
            self.known_users = set(self._fetch_logged_in_users())
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            self.known_users = set()

    def _fetch_logged_in_users(self) -> List[str]:
        if self._platform == "Windows":
            try:
                output = subprocess.check_output("query user", shell=True).decode(errors="ignore")
                return [line.split()[0] for line in output.strip().splitlines()[1:] if line.strip()]
            except Exception as e:
                self.logger.error(f"Failed to query Windows users: {e}")
                return []
        try:
            return list({user.name for user in psutil.users()})
        except Exception as e:
            self.logger.error(f"Failed to retrieve Unix user sessions: {e}")
            return []

    def check_new_logins(self) -> List[str]:
        try:
            current_users = set(self._fetch_logged_in_users())
        except Exception as e:
            self.logger.error(f"Login check failed: {e}")
            return []

        new_logins = sorted(current_users - self.known_users)

        if new_logins:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for user in new_logins:
                self.logger.warning(f"New login detected: {user} at {timestamp}")
                if self._track_history:
                    self.login_history.append({"user": user, "timestamp": timestamp})

        self.known_users = current_users
        return new_logins

    def get_login_history(self) -> Optional[List[Dict[str, str]]]:
        return self.login_history if self._track_history else None
