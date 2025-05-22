import socket
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional


def sweep_host_ports(
    ip: str,
    ports: List[int],
    connect_timeout: float = 0.5,
    banner_timeout: float = 0.3,
    grab_banner: bool = False,
    include_closed: bool = False,
    workers: int = 100,
) -> List[Dict[str, Optional[str]]]:
    ipaddress.ip_address(ip)  # raise ValueError для некорректного IP
    ports = [p for p in ports if 0 < p < 65536]

    def task(port: int) -> Dict[str, Optional[str]]:
        start = time.perf_counter()
        banner = None
        status = "closed"
        try:
            with socket.create_connection((ip, port), timeout=connect_timeout) as sock:
                status = "open"
                if grab_banner:
                    sock.settimeout(banner_timeout)
                    try:
                        banner = sock.recv(1024).decode(errors="ignore").strip() or "N/A"
                    except socket.timeout:
                        banner = "N/A"
        except (ConnectionRefusedError, socket.timeout, OSError):
            pass
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if status == "open" or include_closed:
            return {
                "ip": ip,
                "port": port,
                "status": status,
                "response_time_ms": elapsed,
                "banner": banner,
            }
        return {}

    results: List[Dict[str, Optional[str]]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(task, p) for p in ports]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)
    return sorted(results, key=lambda x: x["port"])
