import socket
import ipaddress
from typing import Optional


def reverse_dns(ip: str) -> Optional[str]:
    if not ip:
        return None
    try:
        ip_obj = ipaddress.ip_address(ip.strip())
        return socket.gethostbyaddr(str(ip_obj))[0]
    except (ValueError, socket.herror, socket.gaierror):
        return None
