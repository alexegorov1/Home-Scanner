import os
import hashlib
from core.config_loader import load_config

class FileMonitor:
    def __init__(self):
        cfg = load_config()
        self.watch_dir = cfg.get("file_monitor", {}).get("watch_dir", "data")
        self.files_hashes = self._get_initial_hashes()

    def _get_initial_hashes(self):
        file_hashes = {}
        for root, _, files in os.walk(self.watch_dir):
            for file in files:
                path = os.path.join(root, file)
                file_hash = self._get_file_hash(path)
                if file_hash:
                    file_hashes[path] = file_hash
        return file_hashes

    def _get_file_hash(self, path):
        hasher = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    def check_files(self):
        modified = []
        current_hashes = self._get_initial_hashes()
        for path, new_hash in current_hashes.items():
            old_hash = self.files_hashes.get(path)
            if old_hash is None or new_hash != old_hash:
                modified.append(path)
        self.files_hashes = current_hashes
        return modified
