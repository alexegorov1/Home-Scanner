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
        except (OSError, IOError, FileNotFoundError) as e:
            return [f"Log read error: {e}"]

        return [
            f"[{r.get('title', 'Unnamed')}] {line.strip()}"
            for line in logs
            for r in self.rules
            if self._match(r.get("detection", {}).get("selection", {}), line)
        ]
