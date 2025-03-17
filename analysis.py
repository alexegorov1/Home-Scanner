import re
from core.logger import Logger

class LogAnalyzer:
    def __init__(self):
        """Initialize the log analyzer with predefined patterns."""
        self.logger = Logger()
        self.patterns = {
            "Failed SSH Login": r"Failed password for",
            "Port Scan": r"Connection attempt from .* on port",
            "Suspicious Command Execution": r"sudo .* unusual activity"
        }

    def analyze_logs(self):
        """Analyze logs for suspicious patterns and return detected anomalies."""
        try:
            logs = self.logger.read_logs()
        except FileNotFoundError:
            return ["Log file not found. No logs to analyze."]
        
        anomalies = []
        for log in logs:
            log = log.strip()  # Strip once for efficiency
            for label, pattern in self.patterns.items():
                if re.search(pattern, log):
                    anomalies.append(f"{label}: {log}")
        
        return anomalies
