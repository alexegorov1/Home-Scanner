import os
import hashlib
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from core.config_loader import load_config


class FileMonitor:
    def __init__(self):
        cfg = load_config()

        self.watch_dir: Path = Path(cfg.get("file_monitor", {}).get("watch_dir", "data")).resolve()
        self.hash_algorithm: str = cfg.get("file_monitor", {}).get("hash_algorithm", "sha256").lower()
        self.track_extensions: List[str] = [ext.lower().lstrip(".") for ext in cfg.get("file_monitor", {}).get("extensions", [])]
        self.include_timestamps: bool = cfg.get("file_monitor", {}).get("track_modified_time", True)
        self.recursive: bool = cfg.get("file_monitor", {}).get("recursive", True)
        self.exclusions: List[str] = cfg.get("file_monitor", {}).get("exclude_paths", [])

        self.files_metadata: Dict[str, Dict[str, Optional[float]]] = {}
        self._init_logger()
        self._validate_config()
        self._initialize_state()

    def _init_logger(self):
        self.logger = logging.getLogger("FileMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_config(self):
        if not self.watch_dir.exists() or not self.watch_dir.is_dir():
            raise ValueError(f"Invalid watch directory: {self.watch_dir}")
        try:
            hashlib.new(self.hash_algorithm)
        except ValueError:
            self.logger.warning(f"Unsupported hash algorithm '{self.hash_algorithm}', falling back to sha256.")
            self.hash_algorithm = "sha256"

    def _initialize_state(self):
        self.logger.info(f"Initializing file metadata for directory: {self.watch_dir}")
        self.files_metadata = self._scan_directory()

    def _is_excluded(self, path: Path) -> bool:
        for pattern in self.exclusions:
            if pattern in str(path):
                return True
        return False

    def _scan_directory(self) -> Dict[str, Dict[str, Optional[float]]]:
        metadata = {}
        if not self.watch_dir.exists():
            self.logger.warning(f"Watch directory does not exist: {self.watch_dir}")
            return metadata

        for root, _, files in os.walk(self.watch_dir, topdown=True):
            for filename in files:
                file_path = Path(root) / filename

                if self.track_extensions and file_path.suffix.lower().lstrip(".") not in self.track_extensions:
                    continue
                if self._is_excluded(file_path):
                    continue

                file_hash = self._calculate_hash(file_path)
                mod_time = self._get_mod_time(file_path) if self.include_timestamps else None

                if file_hash:
                    metadata[str(file_path)] = {
                        "hash": file_hash,
                        "mtime": mod_time
                    }

            if not self.recursive:
                break  # stop descending into subdirs

        return metadata

    def _calculate_hash(self, path: Path) -> Optional[str]:
        try:
            hasher = hashlib.new(self.hash_algorithm)
        except Exception:
            self.logger.warning(f"Falling back to sha256 for hashing.")
            hasher = hashlib.sha256()

        try:
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash file {path}: {e}")
            return None

    def _get_mod_time(self, path: Path) -> Optional[float]:
        try:
            return path.stat().st_mtime
        except Exception as e:
            self.logger.debug(f"Failed to get mtime for {path}: {e}")
            return None

    def check_files(self) -> List[str]:
        """Compares current state to previous metadata, returns list of change descriptions."""
        changes: List[str] = []
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
            self.logger.warning(f"{len(changes)} file change(s) detected.")
            for c in changes:
                self.logger.info(c)
        else:
            self.logger.info("No changes detected in monitored files.")

        self.files_metadata = current_state
        return changes

    def snapshot_to_json(self, output_path: str) -> bool:
        """Exports current state of the monitored directory to a JSON snapshot file."""
        try:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "watch_dir": str(self.watch_dir),
                "hash_algorithm": self.hash_algorithm,
                "track_extensions": list(self.track_extensions),
                "include_timestamps": self.include_timestamps,
                "file_count": len(self.files_metadata),
                "files": self.files_metadata
            }
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            self.logger.info(f"Snapshot exported to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export snapshot: {e}")
            return False

    def reset_metadata(self):
        """Manually re-scan and reset internal file state."""
        self.logger.info("Resetting file monitor state...")
        self.files_metadata = self._scan_directory()
        self.logger.info(f"File monitor state reset with {len(self.files_metadata)} entries.")
