import os
import hashlib
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple
from core.config_loader import load_config


class FileMonitor:
    def __init__(self, config_override: Optional[Dict] = None):
        cfg = config_override or load_config()

        self.watch_dir: Path = Path(cfg.get("file_monitor", {}).get("watch_dir", "data")).resolve()
        self.hash_algorithm: str = cfg.get("file_monitor", {}).get("hash_algorithm", "sha256").lower()
        self.track_extensions: List[str] = [
            ext.lower().lstrip(".") for ext in cfg.get("file_monitor", {}).get("extensions", [])
        ]
        self.include_timestamps: bool = cfg.get("file_monitor", {}).get("track_modified_time", True)
        self.recursive: bool = cfg.get("file_monitor", {}).get("recursive", True)
        self.exclusions: List[str] = [str(Path(p).resolve()) for p in cfg.get("file_monitor", {}).get("exclude_paths", [])]
        self.max_file_size_mb: Optional[int] = cfg.get("file_monitor", {}).get("max_file_size_mb", None)

        self.files_metadata: Dict[str, Dict[str, Union[str, float, None]]] = {}
        self._init_logger()
        self._validate_config()
        self._initialize_state()

    def _init_logger(self):
        self.logger = logging.getLogger("FileMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_config(self):
        if not self.watch_dir.exists() or not self.watch_dir.is_dir():
            raise FileNotFoundError(f"Invalid watch directory: {self.watch_dir}")
        try:
            hashlib.new(self.hash_algorithm)
        except ValueError:
            self.logger.warning(f"Unsupported hash algorithm '{self.hash_algorithm}', using sha256.")
            self.hash_algorithm = "sha256"

    def _initialize_state(self):
        self.logger.info(f"Initializing baseline file state from: {self.watch_dir}")
        self.files_metadata = self._scan_directory()
        self.logger.info(f"Tracking {len(self.files_metadata)} files in baseline.")

    def _is_excluded(self, path: Path) -> bool:
        resolved = str(path.resolve())
        return any(resolved.startswith(excl) for excl in self.exclusions)

    def _is_extension_tracked(self, path: Path) -> bool:
        if not self.track_extensions:
            return True
        return path.suffix.lower().lstrip(".") in self.track_extensions

    def _is_size_allowed(self, path: Path) -> bool:
        if self.max_file_size_mb is None:
            return True
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            return size_mb <= self.max_file_size_mb
        except Exception:
            return False

    def _scan_directory(self) -> Dict[str, Dict[str, Union[str, float, None]]]:
        metadata = {}

        if not self.watch_dir.exists():
            self.logger.error(f"Watch directory missing: {self.watch_dir}")
            return metadata

        for root, _, files in os.walk(self.watch_dir, topdown=True):
            for file in files:
                path = Path(root) / file
                if self._is_excluded(path):
                    continue
                if not self._is_extension_tracked(path):
                    continue
                if not self._is_size_allowed(path):
                    continue

                file_hash = self._calculate_hash(path)
                mod_time = self._get_mod_time(path) if self.include_timestamps else None

                if file_hash:
                    metadata[str(path.resolve())] = {
                        "hash": file_hash,
                        "mtime": mod_time
                    }

            if not self.recursive:
                break  # No deeper traversal

        return metadata

    def _calculate_hash(self, path: Path) -> Optional[str]:
        try:
            hasher = hashlib.new(self.hash_algorithm)
        except Exception as e:
            self.logger.warning(f"Hash init failed ({self.hash_algorithm}), fallback to sha256. Error: {e}")
            hasher = hashlib.sha256()

        try:
            with path.open("rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Cannot hash file {path}: {e}")
            return None

    def _get_mod_time(self, path: Path) -> Optional[float]:
        try:
            return path.stat().st_mtime
        except Exception as e:
            self.logger.debug(f"Cannot get mtime for {path}: {e}")
            return None

    def check_files(self) -> List[str]:
        """Detects file-level changes since last state snapshot."""
        current_state = self._scan_directory()
        changes: List[str] = []

        for path, meta in current_state.items():
            old = self.files_metadata.get(path)
            if not old:
                changes.append(f"[NEW] {path}")
            elif meta["hash"] != old["hash"]:
                changes.append(f"[MODIFIED] {path}")
            elif self.include_timestamps and meta["mtime"] != old.get("mtime"):
                changes.append(f"[TOUCHED] {path}")

        for path in self.files_metadata:
            if path not in current_state:
                changes.append(f"[DELETED] {path}")

        if changes:
            self.logger.warning(f"{len(changes)} change(s) detected in monitored files.")
            for line in changes:
                self.logger.info(line)
        else:
            self.logger.info("No file changes detected.")

        self.files_metadata = current_state
        return changes

    def snapshot_to_json(self, output_path: Union[str, Path]) -> bool:
        """Dump current state of monitored files into a JSON snapshot."""
        try:
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "watch_dir": str(self.watch_dir),
                "hash_algorithm": self.hash_algorithm,
                "recursive": self.recursive,
                "file_count": len(self.files_metadata),
                "files": self.files_metadata
            }
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            self.logger.info(f"Snapshot written to: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")
            return False

    def reset_metadata(self):
        """Manually reinitialize baseline file state."""
        self.logger.info("Resetting baseline file state...")
        self.files_metadata = self._scan_directory()
        self.logger.info(f"Now tracking {len(self.files_metadata)} files.")
