import re
from core.logger import Logger

class LogAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.patterns = {
            "Failed SSH Login": r"Failed password for",
            "Port Scan": r"Connection attempt from .* on port",
            "Suspicious Command Execution": r"sudo .* unusual activity"
        }

    def analyze_logs(self):
        logs = self.logger.read_logs()
        anomalies = []
        for log in logs:
            for label, pattern in self.patterns.items():
                if re.search(pattern, log):
                    anomalies.append(f"{label}: {log.strip()}")
        return anomalies
