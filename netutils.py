import socket
import ipaddress

def reverse_dns(ip: str) -> str:
    try:
        ipaddress.ip_address(ip)
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, ValueError):
        return None
