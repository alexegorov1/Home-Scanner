import asyncio
import socket
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union


class NetworkScanner:
    COMMON_PORTS = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 139: "NetBIOS", 143: "IMAP", 443: "HTTPS",
        445: "SMB", 3306: "MySQL", 3389: "RDP", 5900: "VNC", 8080: "HTTP-Alt"
    }

    POTENTIAL_THREATS = {
        21: "Unencrypted FTP Detected",
        22: "SSH Brute Force Risk",
        23: "Legacy Telnet Exposure",
        25: "SMTP Relay Open",
        53: "DNS Abuse Possibility",
        80: "Public Web Server Found",
        110: "POP3 Credentials Leak",
        139: "NetBIOS Enumeration Risk",
        143: "Unsecured IMAP Detected",
        443: "HTTPS Server Exposed",
        445: "Potential EternalBlue SMB",
        3306: "MySQL Open To Public",
        3389: "RDP Lateral Movement Vector",
        5900: "VNC Exposed Interface",
        8080: "Unsecured Alt-Web Interface"
    }

    def __init__(
        self,
        target: str = "127.0.0.1",
        ports: Optional[List[int]] = None,
        timeout: float = 1.0,
        resolve_hostname: bool = True,
        banner_grab_enabled: bool = True,
        log_file: Optional[Union[str, Path]] = None
    ):
        self.target = target
        self.ports = ports or list(self.COMMON_PORTS.keys())
        self.timeout = timeout
        self.resolve_hostname = resolve_hostname
        self.banner_grab_enabled = banner_grab_enabled
        self.results: List[Dict] = []

        self.logger = logging.getLogger(f"NetworkScanner:{self.target}")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding="utf-8") if log_file else logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def scan(self) -> List[Dict]:
        self.results.clear()

        try:
            if self.resolve_hostname:
                resolved = socket.gethostbyname(self.target)
                self.logger.info(f"Resolved {self.target} to {resolved}")
        except socket.gaierror:
            self.logger.error(f"DNS resolution failed for {self.target}")
            return [{"error": "Unresolved hostname"}]

        self.logger.info(f"Starting async port scan on {self.target}")
        start = datetime.utcnow()
        await self._scan_ports()
        duration = (datetime.utcnow() - start).total_seconds()
        self.logger.info(f"Scan complete in {duration:.2f} seconds. {len(self.results)} open ports detected.")
        return self.results

    async def _scan_ports(self):
        tasks = [self._scan_port(port) for port in self.ports]
        await asyncio.gather(*tasks)

    async def _scan_port(self, port: int):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, port), timeout=self.timeout
            )

            banner = await self._grab_banner(reader) if self.banner_grab_enabled else ""
            writer.close()
            await writer.wait_closed()

            service = self.COMMON_PORTS.get(port, "Unknown")
            threat = self._analyze_threat(port, banner)

            self.results.append({
                "port": port,
                "service": service,
                "banner": banner.strip() if banner else "N/A",
                "threat": threat,
                "timestamp": datetime.utcnow().isoformat(timespec="seconds")
            })

        except asyncio.TimeoutError:
            self.logger.debug(f"Timeout on port {port}")
        except ConnectionRefusedError:
            self.logger.debug(f"Connection refused on port {port}")
        except Exception as e:
            self.logger.warning(f"Unexpected error on port {port}: {e}")

    async def _grab_banner(self, reader) -> str:
        try:
            banner = await asyncio.wait_for(reader.read(1024), timeout=0.5)
            return banner.decode(errors="ignore")
        except Exception as e:
            self.logger.debug(f"Banner grab failed: {e}")
            return ""

    def _analyze_threat(self, port: int, banner: str) -> str:
        base_threat = self.POTENTIAL_THREATS.get(port)
        if not base_threat:
            return f"Open port {port}, unknown service"

        banner_lower = banner.lower()
        indicators = []

        if "unauthorized" in banner_lower or "login" in banner_lower:
            indicators.append("weak auth")
        if any(k in banner_lower for k in ("apache", "nginx", "iis")):
            indicators.append("web server")
        if "openssl" in banner_lower or "tls" in banner_lower:
            indicators.append("tls info")

        if indicators:
            return f"{base_threat} + {' | '.join(indicators)}"

        return base_threat

    def export_results(self, file_path: Union[str, Path]) -> bool:
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("w", encoding="utf-8") as f:
                for entry in sorted(self.results, key=lambda x: x["port"]):
                    line = (
                        f"{entry['timestamp']} | Port {entry['port']}/{entry['service']} | "
                        f"Threat: {entry['threat']} | Banner: {entry['banner']}\n"
                    )
                    f.write(line)

            self.logger.info(f"Scan results exported to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export results to {file_path}: {e}")
            return False

    def summarize(self) -> Dict[str, int]:
        summary = {}
        for entry in self.results:
            threat = entry["threat"]
            summary[threat] = summary.get(threat, 0) + 1
        return summary

    def print_summary(self):
        summary = self.summarize()
        if not summary:
            self.logger.info("No threats detected.")
            return

        self.logger.info("Threat summary:")
        for threat, count in summary.items():
            self.logger.info(f"  {threat}: {count}")
