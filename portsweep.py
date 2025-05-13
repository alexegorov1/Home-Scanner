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
    return list(filter(None, (
        _scan_port(ip, port, timeout, grab_banner, detailed) for port in ports
    )))


def _scan_port(
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
                except:
                    banner = "N/A"
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if detailed:
            return {
                "ip": ip,
                "port": port,
                "status": "open",
                "banner": banner,
                "response_time_ms": elapsed
            }
        return (port, banner) if grab_banner else port
    except:
        return None
