import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str) -> Optional[str]:
    ip = ip.strip()
    if not ip:
        return None
    try:
        ipaddress.ip_address(ip)
        return socket.gethostbyaddr(ip)[0]
    except (ValueError, socket.herror, socket.gaierror, OSError):
        return None
