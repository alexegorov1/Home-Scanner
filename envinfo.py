import os
import platform
import socket
import shutil
import multiprocessing
from typing import Dict


def get_env_info() -> Dict[str, str]:
    try:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "arch": platform.machine(),
            "hostname": platform.node(),
            "ip": _local_ip(),
            "cpus": str(multiprocessing.cpu_count()),
            "cwd": os.getcwd(),
            "virtualized": _is_virtualized(),
            "shell": os.environ.get("SHELL", "unknown"),
            "term": os.environ.get("TERM", "unknown"),
            "disk_gb": _disk_gb(),
            "python": platform.python_version()
        }
    except Exception as e:
        return {"error": str(e)}


def _local_ip() -> str:
    try:
        with socket.create_connection(("8.8.8.8", 80), 1) as s:
            return s.getsockname()[0]
    except:
        return "unknown"


def _is_virtualized() -> str:
    if platform.system() != "Linux":
        return "no"
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            txt = f.read().lower()
            if any(x in txt for x in ("hypervisor", "kvm", "vmware", "xen", "qemu", "vbox")):
                return "yes"
        return "no"
    except:
        return "unknown"


def _disk_gb() -> str:
    try:
        total, _, _ = shutil.disk_usage(os.getcwd())
        return str(round(total / 1_073_741_824, 1))
    except:
        return "unknown"
