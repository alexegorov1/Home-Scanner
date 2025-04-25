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
            "cwd": os.path.abspath(os.getcwd()),
            "virtualized": _detect_virtualization()
        }
    except Exception as e:
        return {"error": f"Failed to gather environment info: {e}"}


def _get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))
            return s.getsockname()[0]
    except Exception:
        return "unknown"


def _detect_virtualization() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                content = f.read().lower()
                if "hypervisor" in content or "kvm" in content or "vmware" in content:
                    return "yes"
        return "no"
    except Exception:
        return "unknown"
