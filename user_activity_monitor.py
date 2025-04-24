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
        self.logger = self._setup_logger()
        self._platform = platform.system()
        self.known_users: Set[str] = set(self._get_logged_in_users())
        self._track_history = track_history
        self.login_history: List[Dict[str, str]] = [] if track_history else []

    def _setup_logger(self) -> logging.Logger:
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

    def _get_logged_in_users(self) -> List[str]:
        try:
            if self._platform == "Windows":
                output = subprocess.check_output("query user", shell=True).decode(errors="ignore")
                return [
                    line.split()[0]
                    for line in output.strip().splitlines()[1:]
                    if line.strip()
                ]
            return list({u.name for u in psutil.users()})
        except Exception as e:
            self.logger.error(f"Failed to retrieve user sessions: {e}")
            return []

    def check_new_logins(self) -> List[str]:
        current_users = set(self._get_logged_in_users())
        new_logins = sorted(current_users - self.known_users)

        if new_logins:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for user in new_logins:
                self.logger.warning(f"New login detected: {user} at {now}")
                if self._track_history:
                    self.login_history.append({"user": user, "timestamp": now})

        self.known_users = current_users
        return new_logins

    def get_login_history(self) -> Optional[List[Dict[str, str]]]:
        return self.login_history if self._track_history else None
