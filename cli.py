def start_cli():
    print("SentinelGuard CLI started. Type 'help' for commands.")
    while True:
        command = input("> ").strip().lower()
        if command == "exit":
            print("Exiting CLI...")
            break
        elif command == "status":
            print("System is running.")
        else:
            print("Unknown command. Type 'help'.")
