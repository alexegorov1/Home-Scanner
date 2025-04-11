import psutil
import logging
from datetime import datetime
from threading import Lock
from pathlib import Path
from typing import List, Optional, Set, Union


class ProcessMonitor:
    def __init__(
        self,
        extra_keywords: Optional[List[str]] = None,
        log_file: Optional[Union[str, Path]] = None,
        track_system_processes: bool = False,
        silent: bool = False,
    ):
        """
        Initializes the process monitor with suspicious keyword list and optional logging.
        :param extra_keywords: List of additional keywords to monitor.
        :param log_file: Path to a file where suspicious detections are logged.
        :param track_system_processes: Whether to include system-level PIDs (0-4).
        :param silent: If True, disables console output.
        """
        base_keywords = {
            "malware", "exploit", "trojan", "keylogger", "meterpreter",
            "cobalt", "empire", "rundll32", "regsvr32", "mshta",
            "powersploit", "netcat", "mimikatz", "beacon", "dump",
            "invoke", "reverse", "shell", "backdoor", "payload"
        }

        if extra_keywords:
            base_keywords.update(map(str.lower, extra_keywords))

        self.suspicious_keywords: Set[str] = base_keywords
        self.track_system = track_system_processes
        self.log_file: Optional[Path] = Path(log_file).resolve() if log_file else None
        self.silent = silent
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
        log_entry = f"[{timestamp}] {message}"

        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with self._lock, self.log_file.open("a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Log write failed: {e}")

        if not self.silent:
            self.logger.warning(log_entry)

    def _normalize(self, value: Optional[Union[str, List[str]]]) -> str:
        if isinstance(value, list):
            return " ".join(value).lower()
        if isinstance(value, str):
            return value.lower()
        return ""

    def check_processes(self, include_cmdline: bool = False, return_raw: bool = False) -> List[Union[str, dict]]:
        """
        Scans all running processes and detects matches against suspicious keywords.
        :param include_cmdline: Whether to inspect command-line arguments.
        :param return_raw: If True, also return full process metadata as dicts.
        :return: List of detection messages or raw result dicts.
        """
        detections = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                pid = proc.info['pid']
                if not self.track_system and pid <= 4:
                    continue

                name = self._normalize(proc.info.get('name'))
                exe = self._normalize(proc.info.get('exe'))
                cmdline = self._normalize(proc.info.get('cmdline'))

                matched_sources = []

                if any(k in name for k in self.suspicious_keywords):
                    matched_sources.append("name")

                if any(k in exe for k in self.suspicious_keywords):
                    matched_sources.append("exe")

                if include_cmdline and any(k in cmdline for k in self.suspicious_keywords):
                    matched_sources.append("cmdline")

                if matched_sources:
                    short_label = name or Path(exe).name or "[unknown]"
                    summary = f"[DETECTED] PID {pid} via {', '.join(matched_sources)}: {short_label}"
                    self._log_detection(summary)

                    if return_raw:
                        detections.append({
                            "pid": pid,
                            "match": matched_sources,
                            "name": name,
                            "exe": exe,
                            "cmdline": cmdline
                        })
                    else:
                        detections.append(summary)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                self.logger.exception(f"[ProcessMonitor] Exception on PID {getattr(proc, 'pid', '?')}: {e}")

        if not detections and not self.silent:
            self.logger.info("Process scan complete: no suspicious activity found.")

        return detections

    def list_keywords(self) -> List[str]:
        """Returns sorted list of current suspicious keywords."""
        return sorted(self.suspicious_keywords)

    def add_keywords(self, new_terms: List[str]):
        """Adds one or more keywords to monitor set."""
        added = 0
        for term in new_terms:
            clean = term.strip().lower()
            if clean and clean not in self.suspicious_keywords:
                self.suspicious_keywords.add(clean)
                added += 1

        if added:
            self.logger.info(f"[ProcessMonitor] Added {added} new keyword(s): {', '.join(new_terms)}")

    def remove_keywords(self, terms: List[str]):
        """Removes specified keywords from the set."""
        removed = 0
        for term in terms:
            clean = term.strip().lower()
            if clean in self.suspicious_keywords:
                self.suspicious_keywords.remove(clean)
                removed += 1

        if removed:
            self.logger.info(f"[ProcessMonitor] Removed {removed} keyword(s): {', '.join(terms)}")
