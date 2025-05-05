import os
import logging
from logging.handlers import RotatingFileHandler, MemoryHandler
import threading

class Logger:
    _lock = threading.Lock()

    def __init__(self, log_file="logs/system.log", max_bytes=5 * 1024 * 1024, backup_count=5, memory_buffer_size=100):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logger = logging.getLogger(f"HomescannerLogger:{log_file}")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.hasHandlers():
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
            file_handler.setFormatter(formatter)
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.INFO)
            memory_handler = MemoryHandler(capacity=memory_buffer_size, flushLevel=logging.ERROR, target=file_handler)
            self.logger.addHandler(memory_handler)
            self.logger.addHandler(stream_handler)

    def log(self, message, level="info"):
        with self._lock:
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message)

    def read_logs(self, lines=100):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [f"Log read error: {e}"]

    def flush(self):
        for handler in self.logger.handlers:
            try:
                handler.flush()
            except:
                pass
