import os
import platform
import socket
import multiprocessing
from typing import Dict


def get_env_info() -> Dict[str, str]:
    info = {}

    try:
        info["os"] = platform.system()
        info["os_version"] = platform.version()
        info["architecture"] = platform.machine()
        info["hostname"] = platform.node()
        info["local_ip"] = _get_local_ip()
        info["cpu_count"] = str(multiprocessing.cpu_count())
        info["cwd"] = os.getcwd()
        info["virtualized"] = _detect_virtualization()
    except Exception as e:
        info["error"] = f"Failed to gather environment info: {e}"

    return info


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def _detect_virtualization() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                if any("hypervisor" in line.lower() for line in f):
                    return "yes"
        return "no"
    except Exception:
        return "unknown"
