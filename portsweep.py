import asyncio
import ipaddress
import random
import socket
import struct
import time
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Union, Optional, Sequence

@dataclass(slots=True)
class ScanResult:
    ip: str
    port: int
    proto: str
    status: str
    latency_ms: float
    banner: Optional[str] = None
    reason: Optional[str] = None

def _parse_ports(items: Iterable[Union[int, str]]) -> List[int]:
    ports: set[int] = set()
    for item in items:
        if isinstance(item, int):
            ports.add(item)
        else:
            part = str(item).strip()
            if "-" in part:
                lo, hi = part.split("-", 1)
                ports.update(range(int(lo), int(hi) + 1))
            else:
                ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)

def _expand_targets(targets: Sequence[str]) -> List[str]:
    expanded: list[str] = []
    for t in targets:
        try:
            net = ipaddress.ip_network(t, strict=False)
            expanded.extend(str(h) for h in net.hosts())
        except ValueError:
            expanded.append(str(ipaddress.ip_address(t)))
    return expanded

async def _tcp_probe(host: str, port: int, timeout: float, grab_banner: bool, banner_timeout: float) -> ScanResult:
    start = time.perf_counter()
    banner = None
    reason = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        status = "open"
        if grab_banner:
            try:
                banner = await asyncio.wait_for(reader.read(1024), timeout=banner_timeout)
                banner = banner.decode(errors="ignore").strip() or "N/A"
            except asyncio.TimeoutError:
                banner = "N/A"
        writer.close()
        await writer.wait_closed()
    except (asyncio.TimeoutError, ConnectionRefusedError):
        status = "closed"
        reason = "timeout" if isinstance(sys.exc_info()[1], asyncio.TimeoutError) else "refused"
    except OSError as e:
        status = "error"
        reason = str(e)
    latency = (time.perf_counter() - start) * 1000
    return ScanResult(host, port, "tcp", status, round(latency, 2), banner, reason)

async def sweep_async(
    targets: Sequence[str] | str,
    ports: Iterable[Union[int, str]],
    tcp: bool = True,
    udp: bool = False,
    timeout: float = 0.5,
    banner: bool = False,
    banner_timeout: float = 0.3,
    include_closed: bool = False,
    shuffle: bool = False,
    concurrency: int = 500,
) -> List[Dict[str, Union[str, int, float, None]]]:
    t_list = _expand_targets([targets] if isinstance(targets, str) else targets)
    p_list = _parse_ports(ports)
    if shuffle:
        random.shuffle(t_list)
        random.shuffle(p_list)

    sem = asyncio.Semaphore(concurrency)
    results: list[ScanResult] = []

    async def guard(coro):
        async with sem:
            res = await coro
            if include_closed or res.status not in {"closed", "error"}:
                results.append(res)

    tasks = []
    for ip in t_list:
        for port in p_list:
            if tcp:
                tasks.append(asyncio.create_task(guard(_tcp_probe(ip, port, timeout, banner, banner_timeout))))
            if udp:
                tasks.append(asyncio.create_task(guard(_udp_probe(ip, port, timeout))))

    await asyncio.gather(*tasks)
    return [asdict(r) for r in sorted(results, key=lambda x: (x.ip, x.port, x.proto))]
