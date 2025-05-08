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
        except Exception as e:
            return [f"Error reading logs: {e}"]
        anomalies = []
        for log in logs:
            entry = log.strip()
            log_lc = entry.lower()
            for rule in self.rules:
                if self._match_rule(rule, log_lc):
                    anomalies.append(f"[{rule.get('title', 'Unnamed Rule')}] {entry}")
        return anomalies

    def _match_rule(self, rule, log_entry):
        try:
            selection = rule.get("detection", {}).get("selection", {})
            for field, value in selection.items():
                if isinstance(value, str):
                    if re.search(re.escape(value), log_entry, re.IGNORECASE):
                        return True
                elif isinstance(value, list):
                    if any(re.search(re.escape(item), log_entry, re.IGNORECASE) for item in value):
                        return True
            return False
        except:
            return False
