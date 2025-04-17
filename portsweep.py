import socket
from typing import List


def sweep_host_ports(ip: str, ports: List[int], timeout: float = 0.5) -> List[int]:
    return [
        port for port in ports
        if _is_port_open(ip, port, timeout)
    ]


def _is_port_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
