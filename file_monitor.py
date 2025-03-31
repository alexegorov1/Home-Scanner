import os
import hashlib
import logging
import time
from datetime import datetime
from core.config_loader import load_config

class FileMonitor:
    def __init__(self):
        cfg = load_config()
        self.watch_dir = cfg.get("file_monitor", {}).get("watch_dir", "data")
        self.hash_algorithm = cfg.get("file_monitor", {}).get("hash_algorithm", "sha256")
        self.track_extensions = cfg.get("file_monitor", {}).get("extensions", [])
        self.include_timestamps = cfg.get("file_monitor", {}).get("track_modified_time", True)
        self.files_metadata = self._get_initial_state()
        self.logger = logging.getLogger("FileMonitor")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _get_initial_state(self):
        metadata = {}
        for root, _, files in os.walk(self.watch_dir):
            for file in files:
                if self.track_extensions and not file.lower().endswith(tuple(self.track_extensions)):
                    continue
                path = os.path.join(root, file)
                file_hash = self._calculate_hash(path)
                modified_time = self._get_mod_time(path) if self.include_timestamps else None
                if file_hash:
                    metadata[path] = {"hash": file_hash, "mtime": modified_time}
        return metadata

    def _calculate_hash(self, path):
        try:
            hasher = hashlib.new(self.hash_algorithm)
        except ValueError:
            hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash file: {path} ({e})")
            return None

    def _get_mod_time(self, path):
        try:
            return os.path.getmtime(path)
        except Exception:
            return None

    def check_files(self):
        changes = []
        current_state = self._get_initial_state()

        for path, meta in current_state.items():
            old_meta = self.files_metadata.get(path)
            if not old_meta:
                changes.append(f"New file detected: {path}")
            elif meta["hash"] != old_meta["hash"]:
                changes.append(f"File modified: {path}")
            elif self.include_timestamps and meta["mtime"] != old_meta.get("mtime"):
                changes.append(f"Timestamp changed: {path}")

        for path in self.files_metadata:
            if path not in current_state:
                changes.append(f"File deleted: {path}")

        if changes:
            self.logger.warning(f"{len(changes)} file system change(s) detected.")
            for c in changes:
                self.logger.info(c)

        self.files_metadata = current_state
        return changes
