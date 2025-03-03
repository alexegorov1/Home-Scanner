import datetime
import os

class Logger:
    def __init__(self, log_file="logs/system.log"):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.log_file = log_file

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        with open(self.log_file, "a") as f:
            f.write(entry)

    def read_logs(self, lines=50):
        with open(self.log_file, "r") as f:
            return f.readlines()[-lines:]
