import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str, timeout: float = 1.0) -> Optional[str]:
    ip = ip.strip()
    if not ip:
        return None
    try:
        ipaddress.ip_address(ip)
        with _temporary_socket_timeout(timeout):
            return socket.gethostbyaddr(ip)[0]
    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None


class _temporary_socket_timeout:
    def __init__(self, timeout: float):
        self.new_timeout = timeout
        self.prev_timeout = socket.getdefaulttimeout()

    def __enter__(self):
        socket.setdefaulttimeout(self.new_timeout)

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.setdefaulttimeout(self.prev_timeout)
