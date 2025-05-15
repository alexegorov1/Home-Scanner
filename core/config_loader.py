import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List

_CFG_CACHE: Dict = {}
_RULES_CACHE: List[Dict] = []

_BASE = Path(__file__).resolve().parent.parent
_CONFIG_FILE = _BASE / "config" / "config.yml"
_RULES_DIR = _BASE / "config"

log = logging.getLogger("ConfigLoader")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def _load_yaml(path: Path) -> Dict:
    if not path.exists():
        log.warning(f"Config file missing: {path}")
        return {}
    with path.open(encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception as e:
            log.error(f"YAML parse failed for {path}: {e}")
            return {}

def load_config(force_reload: bool = False) -> Dict:
    global _CFG_CACHE
    if not _CFG_CACHE or force_reload:
        _CFG_CACHE = _load_yaml(_CONFIG_FILE)
    return _CFG_CACHE

def load_detection_rules(force_reload: bool = False) -> List[Dict]:
    global _RULES_CACHE
    if _RULES_CACHE and not force_reload:
        return _RULES_CACHE

    rules = []
    if _RULES_DIR.exists():
        for yml in _RULES_DIR.glob("*.yml"):
            data = _load_yaml(yml)
            if data:
                rules.append(data)
    else:
        log.warning(f"Rules directory missing: {_RULES_DIR}")

    _RULES_CACHE = rules
    return rules
