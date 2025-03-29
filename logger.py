import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    def __init__(self, log_file="logs/system.log", max_bytes=5 * 1024 * 1024, backup_count=5):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger("HomescannerLogger")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log(self, message, level="info"):
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def read_logs(self, lines=50):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [f"Log read error: {e}"]
