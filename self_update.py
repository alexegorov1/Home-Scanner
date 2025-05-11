import os
import sys
import shutil
import zipfile
import requests
import hashlib
from tempfile import NamedTemporaryFile, TemporaryDirectory
from core.logger import Logger

class SelfUpdater:
    def __init__(self, update_url: str, version_file: str = "VERSION", checksum_file: str = "update.sha256"):
        self.update_url = update_url.rstrip("/")
        self.version_file = version_file
        self.checksum_file = checksum_file
        self.logger = Logger()

    def get_local_version(self) -> str:
        try:
            with open(self.version_file, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            self.logger.log(f"Version file '{self.version_file}' not found. Assuming version 0.0.0", level="warning")
            return "0.0.0"

    def get_remote_version(self) -> str:
        try:
            r = requests.get(f"{self.update_url}/latest_version.txt", timeout=5)
            if r.ok:
                return r.text.strip()
            self.logger.log(f"Failed to fetch remote version. Status: {r.status_code}", level="warning")
            return "0.0.0"
        except Exception as e:
            self.logger.log(f"Remote version fetch error: {e}", level="error")
            return "0.0.0"

    def is_update_available(self) -> bool:
        remote = self.get_remote_version()
        local = self.get_local_version()
        return self._compare_versions(remote, local)

    def _compare_versions(self, v1: str, v2: str) -> bool:
        def parse(v):
            return tuple(map(int, (v.strip().split("."))))
        try:
            return parse(v1) > parse(v2)
        except Exception as e:
            self.logger.log(f"Version comparison error: {e}", level="error")
            return False

    def download_update(self) -> str:
        try:
            r = requests.get(f"{self.update_url}/update.zip", stream=True, timeout=10)
            r.raise_for_status()
            with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                self.logger.log(f"Update downloaded: {tmp.name}", level="info")
                return tmp.name
        except Exception as e:
            self.logger.log(f"Download failed: {e}", level="error")
            return ""

    def verify_checksum(self, file_path: str) -> bool:
        try:
            r = requests.get(f"{self.update_url}/{self.checksum_file}", timeout=5)
            if not r.ok:
                self.logger.log("Checksum file could not be fetched.", level="warning")
                return False
            expected_hash = r.text.strip().split()[0]
            with open(file_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            if actual_hash != expected_hash:
                self.logger.log("Checksum mismatch. Update aborted.", level="error")
                return False
            return True
        except Exception as e:
            self.logger.log(f"Checksum verification error: {e}", level="error")
            return False

    def apply_update(self, zip_path: str):
        if not zip_path or not os.path.isfile(zip_path):
            self.logger.log("Invalid update path.", level="error")
            return
        try:
            with TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)
                self._replace_files(tmpdir)
                self.logger.log("Update applied successfully.", level="info")
        except Exception as e:
            self.logger.log(f"Failed to apply update: {e}", level="error")

    def _replace_files(self, source: str):
        for root, _, files in os.walk(source):
            for file in files:
                src = os.path.join(root, file)
                rel = os.path.relpath(src, source)
                dst = os.path.join(os.getcwd(), rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

    def restart_application(self):
        self.logger.log("Restarting application...", level="info")
        try:
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            self.logger.log(f"Restart failed: {e}", level="error")

    def run(self, auto_restart=True):
        if not self.is_update_available():
            self.logger.log("No update available. Current version is up to date.", level="info")
            return
        self.logger.log("New update detected. Starting download and validation...", level="info")
        zip_path = self.download_update()
        if not zip_path:
            return
        if not self.verify_checksum(zip_path):
            os.remove(zip_path)
            return
        self.apply_update(zip_path)
        os.remove(zip_path)
        if auto_restart:
            self.restart_application()
