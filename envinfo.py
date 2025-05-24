import os
import platform
import socket
import multiprocessing
import shutil
from typing import Dict


def get_env_info() -> Dict[str, str]:
    try:
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "local_ip": _get_local_ip(),
            "cpu_count": str(multiprocessing.cpu_count()),
            "cwd": os.path.realpath(os.getcwd()),
            "virtualized": _detect_virtualization(),
            "shell": os.environ.get("SHELL", "unknown"),
            "terminal": os.environ.get("TERM", "unknown"),
            "disk_total_gb": _get_disk_total_gb(),
            "python_version": platform.python_version(),
        }
    except Exception as e:
        return {"error": str(e)}
