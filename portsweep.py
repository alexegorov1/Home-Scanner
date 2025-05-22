import socket
import time
import ipaddress
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
