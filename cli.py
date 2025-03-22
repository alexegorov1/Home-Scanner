from system.uptime_monitor import UptimeMonitor

def start_cli():
    uptime_monitor = UptimeMonitor()
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
        elif command == "help":
            print("Available commands: status, uptime, exit")
        else:
            print("Unknown command. Type 'help'.")
