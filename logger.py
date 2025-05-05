import os
import logging
from logging.handlers import RotatingFileHandler, MemoryHandler
from datetime import datetime
import threading

class Logger:
    _lock = threading.Lock()

    def __init__(self, log_file="logs/system.log", max_bytes=5 * 1024 * 1024, backup_count=5, memory_buffer_size=100):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger("HomescannerLogger")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.INFO)

            memory_handler = MemoryHandler(
                capacity=memory_buffer_size,
                flushLevel=logging.ERROR,
                target=file_handler
            )

            self.logger.addHandler(memory_handler)
            self.logger.addHandler(stream_handler)

    def log(self, message, level="info"):
        with self._lock:
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

    def read_logs(self, lines=100):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [f"Log read error: {e}"]

    def flush(self):
        for handler in self.logger.handlers:
            if hasattr(handler, "flush"):
                try:
                    handler.flush()
                except Exception:
                    pass
