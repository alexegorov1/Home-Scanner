import psutil

class ProcessMonitor:
    def __init__(self):
        self.suspicious_keywords = ["malware", "exploit", "trojan", "keylogger"]

    def check_processes(self):
        suspicious_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if any(keyword in proc.info['name'].lower() for keyword in self.suspicious_keywords):
                    suspicious_processes.append(f"Suspicious process: {proc.info['name']} (PID {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return suspicious_processes
