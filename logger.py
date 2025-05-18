import os
import sys
import json
import atexit
import signal
import threading
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": record.levelname,
            "component": getattr(record, "component", "generic"),
            "message": record.getMessage(),
            "thread": record.threadName,
            "file": record.pathname,
            "line": record.lineno
        }
        if hasattr(record, "context") and isinstance(record.context, dict):
            log_record["context"] = record.context
        return json.dumps(log_record, ensure_ascii=False)

class Logger:
    _lock = threading.Lock()
    _allowed_levels = {"debug", "info", "warning", "error", "critical"}

    def __init__(self, log_file="logs/system.json.log", max_bytes=5 * 1024 * 1024, backup_count=5):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logger = logging.getLogger(f"HomescannerLogger:{log_file}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if not self.logger.hasHandlers():
            formatter = JSONLogFormatter()

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

        atexit.register(self._flush_on_exit)
        signal.signal(signal.SIGTERM, self._flush_on_exit)
        signal.signal(signal.SIGINT, self._flush_on_exit)

    def log(self, message, level="info", component="core", context=None):
        if not isinstance(message, str) or not message.strip():
            return
        if level.lower() not in self._allowed_levels:
            level = "info"
        if len(message) > 5000:
            message = message[:5000] + "…"

        extra = {
            "component": component,
            "context": context or {}
        }

        with self._lock:
            getattr(self.logger, level.lower())(message.replace("\n", "\\n").replace("\r", "\\r"), extra=extra)

    def read_logs(self, lines=100):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [json.dumps({
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "level": "ERROR",
                "component": "logger",
                "message": f"Log read error: {e}"
            })]

    def _flush_on_exit(self, *_):
        for handler in self.logger.handlers:
            try:
                handler.flush()
            except Exception:
                continue
