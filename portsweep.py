import socket
from typing import List


def sweep_host_ports(ip: str, ports: List[int], timeout: float = 0.5) -> List[int]:
    open_ports = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((ip, port))
                open_ports.append(port)
            except (socket.timeout, ConnectionRefusedError, OSError):
                continue
    return open_ports
