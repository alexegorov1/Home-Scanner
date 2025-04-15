import socket
import ipaddress

def reverse_dns(ip: str) -> Optional[str]:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return socket.gethostbyaddr(str(ip_obj))[0]
    except (socket.herror, socket.gaierror, ValueError):
        return None
