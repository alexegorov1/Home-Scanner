import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str, timeout: float = 1.0) -> Optional[str]:
    try:
        ip = ip.strip()
        if not ip:
            return None

        ipaddress.ip_address(ip)
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        hostname = socket.gethostbyaddr(ip)[0]
        socket.setdefaulttimeout(original_timeout)
        return hostname

    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None
