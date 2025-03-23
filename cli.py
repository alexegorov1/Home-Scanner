from system.uptime_monitor import UptimeMonitor
from monitoring.disk_monitor import DiskMonitor

def start_cli():
    uptime_monitor = UptimeMonitor()
    disk_monitor = DiskMonitor()
    print("Homescanner CLI started. Type 'help' for commands.")
    while True:
        command = input("> ").strip().lower()
        if command == "exit":
            print("Exiting CLI...")
            break
        elif command == "status":
            print("System is running.")
        elif command == "uptime":
            print(uptime_monitor.get_uptime())
        elif command == "disk":
            warnings = disk_monitor.check_disk_usage()
            if warnings:
                for w in warnings:
                    print(w)
            else:
                print("Disk usage is within normal limits.")
        elif command == "help":
            print("Available commands: status, uptime, disk, exit")
        else:
            print("Unknown command. Type 'help'.")
