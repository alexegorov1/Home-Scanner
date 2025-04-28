import socket
import ipaddress
from typing import Optional, Union, Dict, List


def reverse_dns(
    ip: str,
    timeout: float = 1.0,
    detailed: bool = False
) -> Optional[Union[str, Dict[str, Union[str, List[str]]]]]:
    ip = ip.strip()
    if not ip:
        return None
    try:
        ip_obj = ipaddress.ip_address(ip)
        with _SocketTimeout(timeout):
            result = socket.gethostbyaddr(str(ip_obj))
        if detailed:
            return {
                "ip": str(ip_obj),
                "hostname": result[0],
                "aliases": result[1] or []
            }
        return result[0]
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
