import os
import sys
import shutil
import zipfile
import requests
from tempfile import NamedTemporaryFile, TemporaryDirectory
from core.logger import Logger


class SelfUpdater:
    def __init__(self, update_url: str, version_file: str = "VERSION"):
        self.update_url = update_url.rstrip("/")
        self.version_file = version_file
        self.logger = Logger()

    def get_local_version(self) -> str:
        try:
            with open(self.version_file, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "0.0.0"

    def get_remote_version(self) -> str:
        try:
            r = requests.get(f"{self.update_url}/latest_version.txt", timeout=5)
            return r.text.strip() if r.ok else "0.0.0"
        except Exception as e:
            self.logger.log(f"Remote version fetch failed: {e}", level="error")
            return "0.0.0"

    def is_update_available(self) -> bool:
        return self._compare_versions(self.get_remote_version(), self.get_local_version())

    def _compare_versions(self, v1: str, v2: str) -> bool:
        def parse(v): return tuple(map(int, v.split(".")))
        return parse(v1) > parse(v2)

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
            self.logger.log(f"Update download failed: {e}", level="error")
            return ""

    def apply_update(self, zip_path: str):
        if not zip_path or not os.path.isfile(zip_path):
            self.logger.log("Invalid update path.", level="error")
            return
        try:
            with TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(zip_path) as zip_ref:
                    zip_ref.extractall(tmpdir)
                self._replace_files(tmpdir)
                self.logger.log("Update applied.", level="info")
        except Exception as e:
            self.logger.log(f"Apply update failed: {e}", level="error")

    def _replace_files(self, source: str):
        for root, _, files in os.walk(source):
            for file in files:
                src_file = os.path.join(root, file)
                rel = os.path.relpath(src_file, source)
                dst = os.path.join(os.getcwd(), rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src_file, dst)

    def restart_application(self):
        self.logger.log("Restarting...", level="info")
        os.execl(sys.executable, sys.executable, *sys.argv)

    def run(self, auto_restart=True):
        if not self.is_update_available():
            self.logger.log("No update available.", level="info")
            return
        self.logger.log("Update available. Proceeding...", level="info")
        zip_path = self.download_update()
        if zip_path:
            self.apply_update(zip_path)
            if auto_restart:
                self.restart_application()
