import asyncio
import socket
import logging
from datetime import datetime

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

    def __init__(self, target="127.0.0.1", ports=None, timeout=1.0, resolve_hostname=True):
        self.target = target
        self.ports = ports if ports else list(self.COMMON_PORTS.keys())
        self.timeout = timeout
        self.resolve_hostname = resolve_hostname
        self.results = []
        self.banner_grab_enabled = True

    async def scan(self):
        self.results.clear()
        try:
            if self.resolve_hostname:
                resolved_ip = socket.gethostbyname(self.target)
                logging.info(f"Resolved {self.target} to {resolved_ip}")
        except socket.gaierror:
            logging.error(f"[Scanner] DNS resolution failed for {self.target}")
            return [{"error": "Unresolved hostname"}]

        logging.info(f"[Scanner] Starting async scan on {self.target}")
        start_time = datetime.utcnow()
        await self._scan_ports()
        duration = (datetime.utcnow() - start_time).total_seconds()
        logging.info(f"[Scanner] Scan completed in {duration:.2f} seconds")
        return self.results

    async def _scan_ports(self):
        tasks = [self._scan_port(port) for port in self.ports]
        await asyncio.gather(*tasks)

    async def _scan_port(self, port):
        try:
            conn = await asyncio.wait_for(
                asyncio.open_connection(self.target, port),
                timeout=self.timeout
            )
            reader, writer = conn
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
            logging.debug(f"[Scanner] Timeout on port {port}")
        except ConnectionRefusedError:
            logging.debug(f"[Scanner] Connection refused on port {port}")
        except Exception as e:
            logging.warning(f"[Scanner] Unexpected error on port {port}: {e}")

    async def _grab_banner(self, reader):
        try:
            banner = await asyncio.wait_for(reader.read(1024), timeout=0.5)
            return banner.decode(errors="ignore")
        except Exception:
            return ""

    def _analyze_threat(self, port, banner):
        base_threat = self.POTENTIAL_THREATS.get(port)
        if not base_threat:
            return f"Open port {port}, unknown service"

        if banner:
            b = banner.lower()
            if "unauthorized" in b or "login" in b:
                return f"{base_threat} + Possible weak authentication"
            if "apache" in b or "nginx" in b or "iis" in b:
                return f"{base_threat} + Public web stack exposed"
            if "openssl" in b or "tls" in b:
                return f"{base_threat} + TLS stack fingerprinted"
        return base_threat

    def export_results(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in sorted(self.results, key=lambda x: x["port"]):
                    line = f"{entry['timestamp']} | {entry['port']}/{entry['service']} | Threat: {entry['threat']} | Banner: {entry['banner']}\n"
                    f.write(line)
            logging.info(f"[Scanner] Results exported to {file_path}")
        except Exception as e:
            logging.error(f"[Scanner] Failed to export results: {e}")

    def summarize(self):
        summary = {}
        for entry in self.results:
            threat = entry["threat"]
            summary[threat] = summary.get(threat, 0) + 1
        return summary
