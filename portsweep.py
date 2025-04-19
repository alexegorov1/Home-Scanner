import socket
from typing import List


def sweep_host_ports(ip: str, ports: List[int], timeout: float = 0.5) -> List[int]:
    open_ports = []
    for port in ports:
        if _is_port_open(ip, port, timeout):
            open_ports.append(port)
    return open_ports


def _is_port_open(ip: str, port: int, timeout: float) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        return sock.connect_ex((ip, port)) == 0
    except socket.error:
        return False
    finally:
        try:
            sock.close()
        except:
            pass
