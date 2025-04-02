import psutil
import logging
from core.config_loader import load_config

class ProcessMonitor:
    def __init__(self):
        config = load_config()
        self.suspicious_keywords = config.get("process_monitor", {}).get(
            "suspicious_keywords",
            ["malware", "exploit", "trojan", "keylogger", "meterpreter", "backdoor", "rat"]
        )
        self.alert_on_privileged = config.get("process_monitor", {}).get("alert_on_privileged", True)
        self.max_results = config.get("process_monitor", {}).get("max_results", 50)

        self.logger = logging.getLogger("ProcessMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def check_processes(self):
        suspicious = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                if len(suspicious) >= self.max_results:
                    break
                try:
                    name = proc.info.get('name', '') or ''
                    name_lc = name.lower()
                    username = proc.info.get('username', 'unknown')

                    if any(k in name_lc for k in self.suspicious_keywords):
                        suspicious.append(f"Keyword match: {name} (PID {proc.info['pid']}) owned by {username}")

                    if self.alert_on_privileged and username in ['root', 'SYSTEM', 'Administrator']:
                        if "python" in name_lc or "cmd" in name_lc:
                            suspicious.append(f"Privileged suspicious process: {name} (PID {proc.info['pid']}) owned by {username}")

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    self.logger.warning(f"Unexpected error while scanning process: {e}")

        except Exception as global_error:
            self.logger.exception(f"Process enumeration failed: {global_error}")

        if suspicious:
            self.logger.warning(f"{len(suspicious)} suspicious process(es) found.")
        return suspicious
