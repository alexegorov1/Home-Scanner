import os
import hashlib

class FileMonitor:
    def __init__(self, watch_dir="data"):
        self.watch_dir = watch_dir
        self.files_hashes = self.get_initial_hashes()

    def get_initial_hashes(self):
        file_hashes = {}
        for root, _, files in os.walk(self.watch_dir):
            for file in files:
                path = os.path.join(root, file)
                file_hashes[path] = self.get_file_hash(path)
        return file_hashes

    def get_file_hash(self, path):
        hasher = hashlib.md5()
        try:
            with open(path, "rb") as f:
                buf = f.read()
                hasher.update(buf)
        except FileNotFoundError:
            return None
        return hasher.hexdigest()

    def check_files(self):
        modified_files = []
        for path, old_hash in self.files_hashes.items():
            new_hash = self.get_file_hash(path)
            if new_hash and new_hash != old_hash:
                modified_files.append(path)
        return modified_files
