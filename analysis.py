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
            f"[{rule.get('title', 'Unnamed Rule')}] {line.strip()}"
            for line in logs
            for rule in self.rules
            if self._match(rule.get("detection", {}).get("selection", {}), line.strip().lower())
        ]

    def _match(self, selection, text):
        try:
            return any(
                re.search(re.escape(item), text, re.IGNORECASE)
                for val in selection.values()
                for item in (val if isinstance(val, list) else [val])
                if isinstance(item, str)
            )
        except:
            return False
