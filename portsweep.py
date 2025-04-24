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
    results = []
    for port in ports:
        result = _check_port(ip, port, timeout, grab_banner, detailed)
        if result is not None:
            results.append(result)
    return results


def _check_port(
    ip: str,
    port: int,
    timeout: float,
    grab_banner: bool,
    detailed: bool
) -> Optional[Union[int, Tuple[int, str], Dict[str, Union[str, int, float]]]]:
    try:
        start = time.perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            if sock.connect_ex((ip, port)) != 0:
                return None

            banner = ""
            if grab_banner:
                try:
                    sock.settimeout(0.3)
                    data = sock.recv(1024)
                    banner = data.decode(errors="ignore").strip() or "N/A"
                except Exception:
                    banner = "N/A"

        elapsed_ms = (time.perf_counter() - start) * 1000

        if detailed:
            return {
                "ip": ip,
                "port": port,
                "status": "open",
                "banner": banner if grab_banner else "",
                "response_time_ms": round(elapsed_ms, 2)
            }
        return (port, banner) if grab_banner else port

    except socket.error:
        return None
