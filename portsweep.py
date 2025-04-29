import socket
import time
from typing import List, Tuple, Union, Optional, Dict


def sweep_host_ports(
    ip: str,
    ports: List[int],
    timeout: float = 0.5,
    grab_banner: bool = False,
    detailed: bool = False
) -> Union[
    List[int],
    List[Tuple[int, str]],
    List[Dict[str, Union[str, int, float]]]
]:
    return [
        result for port in ports
        if (result := _check_port(ip, port, timeout, grab_banner, detailed)) is not None
    ]


def _check_port(
    ip: str,
    port: int,
    timeout: float,
    grab_banner: bool,
    detailed: bool
) -> Optional[Union[int, Tuple[int, str], Dict[str, Union[str, int, float]]]]:
    try:
        start = time.perf_counter()
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            banner = ""
            if grab_banner:
                try:
                    sock.settimeout(0.3)
                    banner = sock.recv(1024).decode(errors="ignore").strip() or "N/A"
                except Exception:
                    banner = "N/A"
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        if detailed:
            return {
                "ip": ip,
                "port": port,
                "status": "open",
                "banner": banner if grab_banner else "",
                "response_time_ms": elapsed_ms
            }
        return (port, banner) if grab_banner else port
    except Exception:
        return None
