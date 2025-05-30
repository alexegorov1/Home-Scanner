import asyncio
import socket
import logging
import json
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
        log_file: Optional[Union[str, Path]] = None,
        only_known_services: bool = False,
        exclude_ports: Optional[List[int]] = None,
        include_closed_ports: bool = False
    ):
        self.target = target
        self.ports = [p for p in (ports or list(self.COMMON_PORTS.keys())) if not exclude_ports or p not in exclude_ports]
        self.timeout = timeout
        self.resolve_hostname = resolve_hostname
        self.banner_grab_enabled = banner_grab_enabled
        self.only_known_services = only_known_services
        self.include_closed_ports = include_closed_ports
        self.results: List[Dict] = []

        self.logger = logging.getLogger(f"NetworkScanner:{self.target}")
        self.logger.setLevel(logging.INFO)

        if not any(isinstance(h, logging.StreamHandler) or isinstance(h, logging.FileHandler)
                   for h in self.logger.handlers):
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    async def scan(self) -> List[Dict]:
        self.results.clear()
        try:
            if self.resolve_hostname:
                resolved = socket.gethostbyname(self.target)
                self.logger.info(f"Resolved {self.target} to {resolved}")
        except socket.gaierror:
            self.logger.error(f"DNS resolution failed for {self.target}")
            return [{"error": "Unresolved hostname"}]

        self.logger.info(f"Starting port scan on {self.target} with {len(self.ports)} port(s)")
        start = datetime.utcnow()
        await self._scan_ports()
        elapsed = (datetime.utcnow() - start).total_seconds()
        self.logger.info(f"Scan completed in {elapsed:.2f}s — {len(self.results)} open port(s) found.")
        return self.results

    def scan_sync(self) -> List[Dict]:
        try:
            return asyncio.run(self.scan())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.run_until_complete(self.scan())  # fallback for threaded CLI
            return loop.run_until_complete(self.scan())

    async def _scan_ports(self):
        await asyncio.gather(*(self._scan_port(port) for port in self.ports))

    async def _scan_port(self, port: int):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, port), timeout=self.timeout
            )

            banner = await self._grab_banner(reader) if self.banner_grab_enabled else ""
            writer.close()
            await writer.wait_closed()

            result = self._build_result(port, banner)
            if self.only_known_services and result["service"] == "Unknown":
                return
            self.results.append(result)

        except (asyncio.TimeoutError, ConnectionRefusedError):
            if self.include_closed_ports:
                self.results.append({
                    "port": port,
                    "service": self.COMMON_PORTS.get(port, "Unknown"),
                    "status": "closed",
                    "timestamp": datetime.utcnow().isoformat(timespec="seconds")
                })
        except Exception as e:
            self.logger.warning(f"Unexpected error on port {port}: {e}")

    async def _grab_banner(self, reader) -> str:
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
            return data.decode(errors="ignore")
        except Exception as e:
            self.logger.debug(f"Banner grab failed: {e}")
            return ""

    def _build_result(self, port: int, banner: str) -> Dict:
        service = self.COMMON_PORTS.get(port, "Unknown")
        threat = self._analyze_threat(port, banner)
        return {
            "port": port,
            "service": service,
            "banner": banner.strip() or "N/A",
            "threat": threat,
            "status": "open",
            "timestamp": datetime.utcnow().isoformat(timespec="seconds")
        }

    def _analyze_threat(self, port: int, banner: str) -> str:
        base = self.POTENTIAL_THREATS.get(port, f"Open port {port}, unknown service")
        indicators = []

        banner_lc = banner.lower()
        if any(x in banner_lc for x in ("unauthorized", "login", "password")):
            indicators.append("weak auth")
        if any(x in banner_lc for x in ("apache", "nginx", "iis")):
            indicators.append("web server")
        if any(x in banner_lc for x in ("tls", "ssl", "openssl")):
            indicators.append("tls fingerprinted")

        return f"{base} + {' | '.join(indicators)}" if indicators else base

    def export_results_json(self, path: Union[str, Path]) -> bool:
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2)
            self.logger.info(f"Exported results as JSON to {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            return False

    def export_results_text(self, path: Union[str, Path]) -> bool:
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                for r in sorted(self.results, key=lambda x: x["port"]):
                    status = r.get("status", "open")
                    line = (
                        f"{r['timestamp']} | Port {r['port']}/{r['service']} ({status}) | "
                        f"Threat: {r.get('threat', 'N/A')} | Banner: {r.get('banner', '-')}\n"
                    )
                    f.write(line)
            self.logger.info(f"Exported results as text to {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export text: {e}")
            return False

    def summarize(self) -> Dict[str, int]:
        summary = {}
        for r in self.results:
            if r.get("status") == "open":
                threat = r.get("threat", "Uncategorized")
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
