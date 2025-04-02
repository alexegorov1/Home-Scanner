import logging
import os
import platform
from datetime import datetime
from typing import List

if platform.system() == "Windows":
    import subprocess
else:
    import psutil


class UserActivityMonitor:
    def __init__(self):
        self.logger = logging.getLogger("UserActivityMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.known_users = self._get_logged_in_users()

    def _get_logged_in_users(self) -> List[str]:
        users = set()
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output("query user", shell=True).decode()
                for line in output.strip().splitlines()[1:]:
                    parts = line.split()
                    if parts:
                        users.add(parts[0])
            else:
                for u in psutil.users():
                    users.add(u.name)
        except Exception as e:
            self.logger.error(f"Failed to retrieve user sessions: {e}")
        return list(users)

    def check_new_logins(self) -> List[str]:
        current_users = self._get_logged_in_users()
        new_logins = [u for u in current_users if u not in self.known_users]

        if new_logins:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for user in new_logins:
                self.logger.warning(f"New login detected: {user} at {timestamp}")

        self.known_users = current_users
        return new_logins
