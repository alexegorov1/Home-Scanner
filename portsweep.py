import socket
import time
import ipaddress
import random
import functools
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List, Dict, Optional, Union


def _validate_ports(ports: Iterable[Union[int, str]]) -> List[int]:
    uniq: set[int] = set()
    for p in ports:
        try:
            p_int = int(p)
        except (TypeError, ValueError):
            continue
        if 1 <= p_int <= 65535:
            uniq.add(p_int)
    return sorted(uniq)


def _expand_targets(target: str) -> List[str]:
    try:
        net = ipaddress.ip_network(target, strict=False)
        return [str(h) for h in net.hosts()]
    except ValueError:
        ipaddress.ip_address(target)
        return [target]


def sweep(
    target: str | List[str],
    ports: Iterable[Union[int, str]],
    tcp: bool = True,
    udp: bool = False,
    timeout: float = 0.5,
    banner_timeout: float = 0.3,
    banner: bool = False,
    include_closed: bool = False,
    shuffle: bool = False,
    workers: int = 200,
) -> List[Dict[str, Optional[Union[str, float]]]]:
    targets = (
        sum((_expand_targets(t) for t in target), [])
        if isinstance(target, list)
        else _expand_targets(target)
    )
    scan_ports = _validate_ports(ports)
    if shuffle:
        random.shuffle(targets)
        random.shuffle(scan_ports)

    def scan_tcp(host: str, port: int) -> Dict[str, Optional[Union[str, float]]]:
        start = time.perf_counter()
        status = "closed"
        bann = None
        try:
            with socket.create_connection((host, port), timeout=timeout) as s:
                status = "open"
                if banner:
                    s.settimeout(banner_timeout)
                    try:
                        data = s.recv(1024)
                        bann = data.decode(errors="ignore").strip() or "N/A"
                    except socket.timeout:
                        bann = "N/A"
        except (ConnectionRefusedError, socket.timeout, OSError):
            pass
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if status == "open" or include_closed:
            return {
                "ip": host,
                "port": port,
                "proto": "tcp",
                "status": status,
                "latency_ms": elapsed,
                "banner": bann,
            }
        return {}

    def scan_udp(host: str, port: int) -> Dict[str, Optional[Union[str, float]]]:
        start = time.perf_counter()
        status = "open|filtered"
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
                s.settimeout(timeout)
                s.sendto(b"\x00", (host, port))
                s.recvfrom(1024)
                status = "open"
        except socket.timeout:
            status = "open|filtered"
        except OSError:
            status = "closed"
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if status != "closed" or include_closed:
            return {
                "ip": host,
                "port": port,
                "proto": "udp",
                "status": status,
                "latency_ms": elapsed,
                "banner": None,
            }
        return {}
