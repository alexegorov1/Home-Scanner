import os
import re
import json
import glob
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Iterable, Iterator
from core.logger import Logger
from core.config_loader import load_detection_rules

@dataclass
class Selector:
    op: str
    pattern: re.Pattern

@dataclass
class Rule:
    id: str
    title: str
    selectors: List[Selector]
    neg_selectors: List[Selector]
    threshold: int
    window: int

@dataclass
class Finding:
    rule_id: str
    title: str
    ts: str
    file: str
    line: str

class LogAnalyzer:
    STATE_PATH = "cache/analyzer_state.json"
    LOG_MASK = "logs/*.log*"

    def _scan(self) -> Iterator[Finding]:
        for path in sorted(glob.glob(self.LOG_MASK)):
            pos = self.offsets.get(path, 0)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    f.seek(pos)
                    for line in f:
                        ts = datetime.utcnow().isoformat(timespec="seconds")
                        for rule in self.rules:
                            if self._hit(rule, line) and not self._over_threshold(rule, ts):
                                yield Finding(rule.id, rule.title, ts, path, line)
                    self.offsets[path] = f.tell()
            except OSError as e:
                self.logger.log(f"Log read error: {e}", level="error")

    def _hit(self, rule: Rule, line: str) -> bool:
        text = line.lower()
        if rule.neg_selectors and any(sel.pattern.search(text) for sel in rule.neg_selectors):
            return False
        return all(sel.pattern.search(text) for sel in rule.selectors)

    def _over_threshold(self, rule: Rule, ts: str) -> bool:
        if not rule.window:
            return False
        bucket = int(datetime.fromisoformat(ts).timestamp()) // rule.window
        counter = self.hit_counter[rule.id]
        counter[bucket] = counter.get(bucket, 0) + 1
        return counter[bucket] > rule.threshold

    def _build_selectors(self, block: Dict) -> List[Selector]:
        result = []
        for value in block.values():
            vals = value if isinstance(value, list) else [value]
            for v in vals:
                v = str(v)
                if v.startswith("/") and v.endswith("/"):
                    pat = re.compile(v.strip("/"), re.I)
                else:
                    pat = re.compile(re.escape(v), re.I)
                result.append(Selector("regex", pat))
        return result

    def _load_state(self):
        if os.path.exists(self.STATE_PATH):
            try:
                data = json.load(open(self.STATE_PATH, encoding="utf-8"))
                self.offsets = data.get("offsets", {})
                self.hit_counter = defaultdict(dict, {k: {int(b): c for b, c in v.items()} for k, v in data.get("hits", {}).items()})
            except Exception:
                self.offsets, self.hit_counter = {}, defaultdict(dict)

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self.STATE_PATH), exist_ok=True)
            data = {"offsets": self.offsets, "hits": self.hit_counter}
            json.dump(data, open(self.STATE_PATH, "w", encoding="utf-8"))
        except Exception as e:
            self.logger.log(f"State save failed: {e}", level="warning")
