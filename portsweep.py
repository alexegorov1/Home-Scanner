import socket
import time
from typing import List, Tuple, Union, Optional, Dict


def sweep_host_ports(
    ip: str,
    ports: List[int],
    timeout: float = 0.5,
    grab_banner: bool = False,
    detailed: bool = False
) -> Union[
    List[int],
    List[Tuple[int, str]],
    List[Dict[str, Union[str, int, float]]]
]:
    results = []
    for port in ports:
        result = _scan_port(ip, port, timeout, grab_banner, detailed)
        if result is not None:
            results.append(result)
    return results

