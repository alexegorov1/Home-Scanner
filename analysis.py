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
class Finding:
    rule_id: str
    title: str
    ts: str
    file: str
    line: str

class LogAnalyzer:
    STATE_PATH = "cache/analyzer_state.json"
    LOG_MASK = "logs/*.log*"

    def __init__(self):
        self.logger = Logger()
        self.rules: List[Rule] = self._compile_rules(load_detection_rules())
        self.offsets: Dict[str, int] = {}
        self.hit_counter: Dict[str, Dict[int, int]] = defaultdict(dict)
        self._load_state()

    def analyze(self, fmt: str = "plain") -> Iterable[str]:
        start = time.time()
        for finding in self._scan():
            if fmt == "json":
                yield json.dumps(asdict(finding), ensure_ascii=False)
            else:
                yield f"[{finding.rule_id}] {finding.line.strip()}"
        self._save_state()
        self.stats = {
            "duration_ms": round((time.time() - start) * 1000),
            "rules": len(self.rules),
            "files": len(self.offsets),
        }

    def _hit(self, rule: Rule, line: str) -> bool:
        text = line.lower()
        if rule.neg_selectors and any(sel.pattern.search(text) for sel in rule.neg_selectors):
            return False
        return all(sel.pattern.search(text) for sel in rule.selectors)
        
    def _load_state(self):
        if os.path.exists(self.STATE_PATH):
            try:
                data = json.load(open(self.STATE_PATH, encoding="utf-8"))
                self.offsets = data.get("offsets", {})
                self.hit_counter = defaultdict(dict, {k: {int(b): c for b, c in v.items()} for k, v in data.get("hits", {}).items()})
            except Exception:
                self.offsets, self.hit_counter = {}, defaultdict(dict)
