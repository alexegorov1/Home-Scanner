import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str, timeout: float = 1.0) -> Optional[str]:
    if not ip:
        return None

    ip = ip.strip()
    if not ip:
        return None

    try:
        ip_obj = ipaddress.ip_address(ip)
        with _SocketTimeout(timeout):
            return socket.gethostbyaddr(str(ip_obj))[0]
    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None


class _SocketTimeout:
    __slots__ = ("_timeout", "_original")

    def __init__(self, timeout: float):
        self._timeout = timeout
        self._original = socket.getdefaulttimeout()

    def __enter__(self):
        socket.setdefaulttimeout(self._timeout)

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.setdefaulttimeout(self._original)
