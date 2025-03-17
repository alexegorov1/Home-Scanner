import psutil

class ProcessMonitor:
    def __init__(self):
        """Initialize the process monitor with predefined suspicious keywords."""
        self.suspicious_keywords = ["malware", "exploit", "trojan", "keylogger"]

    def check_processes(self):
        """Scan running processes for suspicious names."""
        suspicious_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process_name = proc.info.get('name', '').lower()  # Handle None case safely
                if any(keyword in process_name for keyword in self.suspicious_keywords):
                    suspicious_processes.append(f"Suspicious process: {proc.info['name']} (PID {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes that no longer exist or cannot be accessed
                continue
        return suspicious_processes
