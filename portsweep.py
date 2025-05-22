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
    return list(filter(None, (
        _scan_port(ip, port, timeout, grab_banner, detailed) for port in ports
    )))

        return (port, banner) if grab_banner else port
    except:
        return None
