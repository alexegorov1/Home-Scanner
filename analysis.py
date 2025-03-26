import re
from core.logger import Logger
from core.config_loader import load_detection_rules

class LogAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.rules = load_detection_rules()

    def analyze_logs(self):
        try:
            logs = self.logger.read_logs()
        except FileNotFoundError:
            return ["Log file not found. No logs to analyze."]

        anomalies = []
        for log in logs:
            log = log.strip().lower()
            for rule in self.rules:
                pattern = self._extract_pattern(rule)
                if pattern and re.search(pattern, log, re.IGNORECASE):
                    anomalies.append(f"[{rule.get('title', 'Unnamed Rule')}] {log}")
        return anomalies

    def _extract_pattern(self, rule):
        try:
            detection = rule.get("detection", {})
            for field, value in detection.get("selection", {}).items():
                if isinstance(value, str):
                    return re.escape(value)
                elif isinstance(value, list):
                    return "|".join([re.escape(v) for v in value])
        except Exception:
            return None
