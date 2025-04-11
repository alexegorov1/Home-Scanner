import psutil
import logging
from datetime import datetime
from threading import Lock
from pathlib import Path
from typing import List, Optional, Set


class ProcessMonitor:
    def __init__(
        self,
        extra_keywords: Optional[List[str]] = None,
        log_file: Optional[str] = None,
        track_system_processes: bool = False,
    ):
        """
        Initializes the process monitor with predefined suspicious keywords.
        :param extra_keywords: Optional list of additional suspicious terms.
        :param log_file: Optional path to store detection logs.
        :param track_system_processes: If False, skips PID 0–4 (system idle, kernel).
        """
        default_keywords = {
            "malware", "exploit", "trojan", "keylogger",
            "meterpreter", "cobalt", "empire", "rundll32",
            "regsvr32", "mshta", "powersploit", "netcat",
        }

        if extra_keywords:
            default_keywords.update(map(str.lower, extra_keywords))

        self.suspicious_keywords: Set[str] = default_keywords
        self.log_file: Optional[Path] = Path(log_file).resolve() if log_file else None
        self.track_system = track_system_processes
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
        log_line = f"[{timestamp}] {message}"

        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with self._lock, self.log_file.open("a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Failed to write log: {e}")
        else:
            self.logger.warning(log_line)

    def check_processes(self, include_cmdline: bool = False) -> List[str]:
        """
        Scans running processes for suspicious patterns.
        :param include_cmdline: Whether to scan command-line arguments.
        :return: List of detection messages.
        """
        detections: List[str] = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                pid = proc.info['pid']
                if not self.track_system and pid <= 4:
                    continue

                name = (proc.info.get('name') or "").lower()
                exe = (proc.info.get('exe') or "").lower()
                cmdline = " ".join(proc.info.get('cmdline') or []).lower()

                indicators = []

                if any(k in name for k in self.suspicious_keywords):
                    indicators.append("name")

                if any(k in exe for k in self.suspicious_keywords):
                    indicators.append("exe")

                if include_cmdline and any(k in cmdline for k in self.suspicious_keywords):
                    indicators.append("cmdline")

                if indicators:
                    summary = (
                        f"[DETECTED] PID {pid} via {', '.join(indicators)}: "
                        f"{name or Path(exe).name or '[unknown]'}"
                    )
                    detections.append(summary)
                    self._log_detection(summary)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Failed on PID {getattr(proc, 'pid', '?')}: {e}")

        if not detections:
            self.logger.info("Process check complete: no suspicious activity found.")

        return detections

    def list_keywords(self) -> List[str]:
        return sorted(self.suspicious_keywords)

    def add_keywords(self, new_terms: List[str]):
        for term in new_terms:
            self.suspicious_keywords.add(term.lower().strip())
        self.logger.info(f"ProcessMonitor: added {len(new_terms)} new keyword(s).")
