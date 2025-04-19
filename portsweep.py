import socket
from typing import List


def sweep_host_ports(ip: str, ports: List[int], timeout: float = 0.5) -> List[int]:
    return [port for port in ports if _is_port_open(ip, port, timeout)]


def _is_port_open(ip: str, port: int, timeout: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((ip, port)) == 0
    except socket.error:
        return False
    finally:
        sock.close()
