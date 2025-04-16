import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str, timeout: float = 1.0) -> Optional[str]:
    ip = ip.strip()
    if not ip:
        return None
    try:
        ipaddress.ip_address(ip)
        prev_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            return socket.gethostbyaddr(ip)[0]
        finally:
            socket.setdefaulttimeout(prev_timeout)
    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None
