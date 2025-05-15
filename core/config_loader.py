# core/config_loader.py
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


