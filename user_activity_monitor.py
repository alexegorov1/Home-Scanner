import logging
import platform
from datetime import datetime
from typing import List, Set, Optional

if platform.system() == "Windows":
    import subprocess
else:
    import psutil


class UserActivityMonitor:
    def __init__(self, track_history: bool = False):
        self.logger = logging.getLogger("UserActivityMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self._platform = platform.system()
        self.known_users: Set[str] = set(self._get_logged_in_users())
        self.login_history: List[dict] = [] if track_history else None

    def _get_logged_in_users(self) -> List[str]:
        try:
            if self._platform == "Windows":
                output = subprocess.check_output("query user", shell=True).decode(errors="ignore")
                return [line.split()[0] for line in output.strip().splitlines()[1:] if line.strip()]
            else:
                return list({u.name for u in psutil.users()})
        except Exception as e:
            self.logger.error(f"Failed to retrieve user sessions: {e}")
            return []

    def check_new_logins(self) -> List[str]:
        current_users = set(self._get_logged_in_users())
        new_logins = sorted(current_users - self.known_users)

        if new_logins:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for user in new_logins:
                self.logger.warning(f"New login detected: {user} at {timestamp}")
                if self.login_history is not None:
                    self.login_history.append({"user": user, "timestamp": timestamp})

        self.known_users = current_users
        return new_logins

    def get_login_history(self) -> Optional[List[dict]]:
        return self.login_history if self.login_history is not None else None
