import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str, timeout: float = 1.0) -> Optional[str]:
    ip = ip.strip()
    if not ip:
        return None

    try:
        with _SocketTimeout(timeout):
            return socket.gethostbyaddr(str(ipaddress.ip_address(ip)))[0]
    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None


class _SocketTimeout:
    __slots__ = ("timeout", "original")

    def __init__(self, timeout: float):
        self.timeout = timeout
        self.original = socket.getdefaulttimeout()

    def __enter__(self):
        socket.setdefaulttimeout(self.timeout)

    def __exit__(self, *_):
        socket.setdefaulttimeout(self.original)
