import socket
from typing import List


def sweep_host_ports(ip: str, ports: List[int], timeout: float = 0.5) -> List[int]:
    return [port for port in ports if is_port_open(ip, port, timeout)]


def is_port_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((ip, port)) == 0
    except OSError:
        return False
