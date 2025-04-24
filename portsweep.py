import socket
from typing import List, Tuple, Union, Optional, Dict


def sweep_host_ports(
    ip: str,
    ports: List[int],
    timeout: float = 0.5,
    grab_banner: bool = False,
    detailed: bool = False
) -> Union[List[int], List[Tuple[int, str]], List[Dict[str, Union[int, str]]]]:
    results = []
    for port in ports:
        banner = _try_port(ip, port, timeout, grab_banner)
        if banner is not None:
            if detailed:
                results.append({
                    "port": port,
                    "status": "open",
                    "banner": banner if grab_banner else ""
                })
            else:
                results.append((port, banner) if grab_banner else port)
    return results


def _try_port(ip: str, port: int, timeout: float, grab_banner: bool) -> Optional[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        if sock.connect_ex((ip, port)) == 0:
            if grab_banner:
                try:
                    sock.settimeout(0.3)
                    data = sock.recv(1024)
                    return data.decode(errors="ignore").strip() or "N/A"
                except Exception:
                    return "N/A"
            return ""
    except socket.error:
        return None
    finally:
        sock.close()
