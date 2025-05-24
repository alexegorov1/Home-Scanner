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

    def _match(self, selection, text):
        if not selection or not isinstance(selection, dict):
            return False
        lowered = text.lower()
        try:
            return any(
                any(re.search(re.escape(s), lowered, re.IGNORECASE)
                    for s in v if isinstance(v, list))
                if isinstance(v, list)
                else re.search(re.escape(v), lowered, re.IGNORECASE)
                for v in selection.values()
            )
        except Exception:
            return False
