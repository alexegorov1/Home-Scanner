import os
import platform
import socket
import multiprocessing
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
            "cwd": os.getcwd(),
            "virtualized": _detect_virtualization()
        }
    except Exception as e:
        return {"error": str(e)}


def _get_local_ip() -> str:
    try:
        with socket.create_connection(("8.8.8.8", 80), timeout=2) as s:
            return s.getsockname()[0]
    except Exception:
        return "unknown"


def _detect_virtualization() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                content = f.read().lower()
                if any(term in content for term in ("hypervisor", "kvm", "vmware", "xen")):
                    return "yes"
        return "no"
    except Exception:
        return "unknown"
