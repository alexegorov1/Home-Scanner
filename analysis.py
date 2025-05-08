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
        except (FileNotFoundError, IOError):
            return ["Log file not found. No logs to analyze."]
        except Exception as e:
            return [f"Error reading logs: {e}"]
        return [
            f"[{rule.get('title', 'Unnamed Rule')}] {entry.strip()}"
            for entry in logs
            for rule in self.rules
            if self._match_rule(rule, entry.strip().lower())
        ]

    def _match_rule(self, rule, log_entry):
        try:
            selection = rule.get("detection", {}).get("selection", {})
            return any(
                isinstance(value, str) and re.search(re.escape(value), log_entry, re.IGNORECASE)
                or isinstance(value, list) and any(re.search(re.escape(v), log_entry, re.IGNORECASE) for v in value)
                for value in selection.values()
            )
        except:
            return False
