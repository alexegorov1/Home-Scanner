import os
import sys
import json
import atexit
import signal
import threading
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler

class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "component": getattr(record, "component", "generic"),
            "event_type": getattr(record, "event_type", "log"),
            "thread": record.threadName,
            "source": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        }

        if hasattr(record, "context") and isinstance(record.context, dict):
            payload["context"] = record.context

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

class Logger:
    _lock = threading.Lock()
    _valid_levels = {"debug", "info", "warning", "error", "critical"}
    _valid_events = {"log", "scan", "alert", "db", "file", "user", "uptime", "network", "internal"}

    def __init__(self, log_file="logs/system.json.log", max_bytes=5 * 1024 * 1024, backup_count=5):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger(f"HomescannerLogger:{log_file}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if not self.logger.handlers:
            formatter = JSONLogFormatter()
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.INFO)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

        atexit.register(self._flush)
        signal.signal(signal.SIGINT, self._flush)
        signal.signal(signal.SIGTERM, self._flush)

    def log(self, message, level="info", component="core", event_type="log", context=None, exc: Exception = None):
        if not isinstance(message, str) or not message.strip():
            return

        level = level.lower()
        if level not in self._valid_levels:
            level = "info"

        event_type = event_type.lower()
        if event_type not in self._valid_events:
            event_type = "log"

        extra = {
            "component": component,
            "event_type": event_type,
            "context": context or {}
        }

        with self._lock:
            if exc:
                self.logger.log(getattr(logging, level.upper(), logging.INFO), message, extra=extra, exc_info=exc)
            else:
                self.logger.log(getattr(logging, level.upper(), logging.INFO), message, extra=extra)

    def read_logs(self, lines=100):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-lines:]
        except Exception as e:
            return [json.dumps({
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "level": "ERROR",
                "component": "logger",
                "event_type": "internal",
                "message": f"Log read error: {str(e)}"
            })]

    def _flush(self, *_):
        for handler in self.logger.handlers:
            try:
                handler.flush()
            except Exception:
                continue
