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


def _get_local_ip() -> str:
    try:
        with socket.create_connection(("8.8.8.8", 80), timeout=1) as s:
            return s.getsockname()[0]
    except Exception:
        return "unknown"


def _detect_virtualization() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                text = f.read().lower()
                if any(term in text for term in ("hypervisor", "kvm", "vmware", "xen", "qemu", "vbox")):
                    return "yes"
        return "no"
    except Exception:
        return "unknown"


def _get_disk_total_gb() -> str:
    try:
        total, _, _ = shutil.disk_usage(os.getcwd())
        return str(round(total / (1024 ** 3), 1))
    except Exception:
        return "unknown"
