import os
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from core.config_loader import load_config


class FileMonitor:
    def __init__(self):
        cfg = load_config()

        self.watch_dir = Path(cfg.get("file_monitor", {}).get("watch_dir", "data")).resolve()
        self.hash_algorithm = cfg.get("file_monitor", {}).get("hash_algorithm", "sha256").lower()
        self.track_extensions = set(ext.lower() for ext in cfg.get("file_monitor", {}).get("extensions", []))
        self.include_timestamps = cfg.get("file_monitor", {}).get("track_modified_time", True)

        self.files_metadata: Dict[str, Dict[str, Optional[float]]] = {}
        self._init_logger()
        self._validate_config()
        self._initialize_state()

    def _init_logger(self):
        self.logger = logging.getLogger("FileMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_config(self):
        if not self.watch_dir.exists() or not self.watch_dir.is_dir():
            raise ValueError(f"Invalid watch directory: {self.watch_dir}")
        try:
            hashlib.new(self.hash_algorithm)
        except ValueError:
            self.logger.warning(f"Unsupported hash algorithm '{self.hash_algorithm}', defaulting to sha256")
            self.hash_algorithm = "sha256"

    def _initialize_state(self):
        self.files_metadata = self._scan_directory()

    def _scan_directory(self) -> Dict[str, Dict[str, Optional[float]]]:
        metadata = {}
        for root, _, files in os.walk(self.watch_dir, topdown=True):
            for filename in files:
                filepath = Path(root) / filename
                if self.track_extensions and filepath.suffix.lower().lstrip(".") not in self.track_extensions:
                    continue

                hash_value = self._calculate_hash(filepath)
                mod_time = self._get_mod_time(filepath) if self.include_timestamps else None

                if hash_value is not None:
                    metadata[str(filepath)] = {
                        "hash": hash_value,
                        "mtime": mod_time,
                    }
        return metadata

    def _calculate_hash(self, path: Path) -> Optional[str]:
        try:
            hasher = hashlib.new(self.hash_algorithm)
        except Exception:
            hasher = hashlib.sha256()

        try:
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash file: {path} — {e}")
            return None

    def _get_mod_time(self, path: Path) -> Optional[float]:
        try:
            return path.stat().st_mtime
        except Exception:
            return None

    def check_files(self):
        changes = []
        current_state = self._scan_directory()

        for path, new_meta in current_state.items():
            old_meta = self.files_metadata.get(path)
            if not old_meta:
                changes.append(f"New file detected: {path}")
            elif new_meta["hash"] != old_meta["hash"]:
                changes.append(f"File modified: {path}")
            elif self.include_timestamps and new_meta["mtime"] != old_meta.get("mtime"):
                changes.append(f"Timestamp changed: {path}")

        for old_path in self.files_metadata:
            if old_path not in current_state:
                changes.append(f"File deleted: {old_path}")

        if changes:
            self.logger.warning(f"{len(changes)} file system change(s) detected.")
            for change in changes:
                self.logger.info(change)

        self.files_metadata = current_state
        return changes

    def snapshot_to_json(self, output_path: str):
        try:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "watch_dir": str(self.watch_dir),
                "files": self.files_metadata,
            }
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                import json
                json.dump(snapshot, f, indent=2)
            self.logger.info(f"Snapshot written to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to write snapshot: {e}")
