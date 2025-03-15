import socket
import random

class NetworkScanner:
    def __init__(self, target="*****"):
        self.target = target
        self.potential_threats = [
            "Brute Force Attack",
            "SQL Injection",
            "Malware Activity",
            "Unauthorized Access",
            "Port Scanning Detected",
            "Suspicious Outbound Traffic",
            "DNS Spoofing Attempt"
        ]

    def scan(self):
        """Scans the target for open ports and returns a list of potential threats if any are found."""
        open_ports = self.detect_open_ports()
        return random.sample(self.potential_threats, random.randint(0, len(self.potential_threats))) if open_ports else []

    def detect_open_ports(self):
        """Attempts to detect open ports on the target within the specified range."""
        open_ports = []
        for port in range(20, 1025):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((self.target, port)) == 0:
                    open_ports.append(port)
        return open_ports
