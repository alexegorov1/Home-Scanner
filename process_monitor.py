import psutil
import logging
from datetime import datetime
from threading import Lock

class ProcessMonitor:
    def __init__(self, extra_keywords=None, log_file=None):
        """
        Initialize the process monitor with predefined suspicious keywords.
        :param extra_keywords: Optional list of additional suspicious terms.
        :param log_file: Optional path to log detected processes.
        """
        default_keywords = {"malware", "exploit", "trojan", "keylogger", "meterpreter", "cobalt", "empire"}
        if extra_keywords:
            default_keywords.update(map(str.lower, extra_keywords))
        self.suspicious_keywords = default_keywords
        self.log_file = log_file
        self._lock = Lock()

    def _log_detection(self, message: str):
        if not self.log_file:
            logging.warning(f"[ProcessMonitor] {message}")
            return
        try:
            with self._lock, open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.utcnow().isoformat(timespec='seconds')}] {message}\n")
        except Exception as e:
            logging.exception(f"[ProcessMonitor] Failed to write log: {e}")

    def check_processes(self, include_cmdline=False):
        """
        Scan running processes for suspicious names or command-line args.
        :param include_cmdline: If True, also inspect the command line of processes.
        :return: List of detected suspicious processes (as formatted strings).
        """
        suspicious = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                pid = proc.info['pid']
                name = (proc.info.get('name') or "").lower()
                exe = (proc.info.get('exe') or "").lower()
                cmdline = " ".join(proc.info.get('cmdline') or []).lower()

                detection_sources = []

                if any(k in name for k in self.suspicious_keywords):
                    detection_sources.append("name")

                if any(k in exe for k in self.suspicious_keywords):
                    detection_sources.append("exe")

                if include_cmdline and any(k in cmdline for k in self.suspicious_keywords):
                    detection_sources.append("cmdline")

                if detection_sources:
                    summary = f"[DETECTED] Suspicious process (PID {pid}) via {', '.join(detection_sources)}: {name or exe or '[unknown]'}"
                    suspicious.append(summary)
                    self._log_detection(summary)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logging.exception(f"[ProcessMonitor] Unexpected error scanning PID {proc.pid}: {e}")

        return suspicious
