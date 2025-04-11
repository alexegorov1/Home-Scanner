import psutil
import logging
from datetime import datetime
from threading import Lock
from pathlib import Path
from typing import List, Optional, Set


class ProcessMonitor:
    def __init__(self, extra_keywords: Optional[List[str]] = None, log_file: Optional[str] = None):
        """
        Initialize the process monitor with predefined suspicious keywords.
        :param extra_keywords: Optional list of additional suspicious terms.
        :param log_file: Optional path to log detected processes.
        """
        base_keywords = {
            "malware", "exploit", "trojan", "keylogger",
            "meterpreter", "cobalt", "empire", "shellcode",
            "powersploit", "rundll32", "regsvr32", "mshta",
        }

        if extra_keywords:
            base_keywords.update(map(str.lower, extra_keywords))

        self.suspicious_keywords: Set[str] = base_keywords
        self.log_file: Optional[Path] = Path(log_file).resolve() if log_file else None
        self._lock = Lock()

        self.logger = logging.getLogger("ProcessMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log_detection(self, message: str):
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        entry = f"[{timestamp}] {message}"

        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with self._lock, self.log_file.open("a", encoding="utf-8") as f:
                    f.write(entry + "\n")
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Failed to write to log file: {e}")
        else:
            self.logger.warning(entry)

    def check_processes(self, include_cmdline: bool = False) -> List[str]:
        """
        Scan running processes for suspicious names or command-line arguments.
        :param include_cmdline: If True, also inspect the command line of processes.
        :return: List of detected suspicious processes (formatted strings).
        """
        suspicious: List[str] = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                pid = proc.info['pid']
                name = (proc.info.get('name') or "").lower()
                exe = (proc.info.get('exe') or "").lower()
                cmdline = " ".join(proc.info.get('cmdline') or []).lower()

                match_sources = []

                if any(k in name for k in self.suspicious_keywords):
                    match_sources.append("name")

                if any(k in exe for k in self.suspicious_keywords):
                    match_sources.append("exe")

                if include_cmdline and any(k in cmdline for k in self.suspicious_keywords):
                    match_sources.append("cmdline")

                if match_sources:
                    short_name = name or Path(exe).name or "[unknown]"
                    summary = (
                        f"[DETECTED] Suspicious process (PID {pid}) via {', '.join(match_sources)}: {short_name}"
                    )
                    suspicious.append(summary)
                    self._log_detection(summary)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Unexpected error for PID {proc.pid}: {e}")

        if not suspicious:
            self.logger.info("Process scan completed: no suspicious activity detected.")

        return suspicious

    def list_tracked_keywords(self) -> List[str]:
        """
        Return sorted list of all keywords currently used for detection.
        """
        return sorted(self.suspicious_keywords)

    def add_keyword(self, keyword: str):
        """
        Dynamically add a new keyword to detection list.
        """
        keyword = keyword.lower().strip()
        if keyword:
            self.suspicious_keywords.add(keyword)
            self.logger.info(f"Keyword added to process monitor: '{keyword}'")
