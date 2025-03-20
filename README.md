Home-Scanner is a security monitoring system designed to keep an eye on network activity, analyze logs for anomalies, detect suspicious processes, track file modifications, and manage security incidents. It also includes an API server for logging and retrieving incidents.

This thing is built to run continuously, scanning for threats and flagging anything shady. It monitors the system, logs suspicious behavior, and fires off alerts when something looks off. Whether it's network intrusions, sketchy logs, or unauthorized file changes, it watches everything and keeps a record of incidents.

How It Works
The main script fires up several key components. The NetworkScanner checks for open ports and detects potential threats. The LogAnalyzer scans system logs for suspicious patterns. The ProcessMonitor watches running processes, looking for anything that smells like malware. The FileMonitor keeps track of changes to files, spotting unauthorized modifications. All this data gets logged, and when something suspicious pops up, the AlertManager sends notifications. Everything is stored in an IncidentDatabase, and the API server lets you pull incident reports when needed.

The system runs in an infinite loop, checking for new threats every minute. If something nasty is detected, it gets logged, an alert is fired off, and the incident is stored in the database. The API lets you access these incidents through a simple HTTP request. There's also a CLI for interacting with the system manually.

Components:
Network Scanner
The scanner sweeps the network for open ports and potential intrusions. It detects common attack vectors like brute force attempts, SQL injections, and unauthorized access. If an open port is found, it randomly assigns a potential threat from a predefined list.

Log Analyzer
Reads system logs and searches for patterns indicating unauthorized access attempts or suspicious commands. Uses regex-based detection for common attack signatures. If a match is found, it's flagged as an anomaly and logged.

Process Monitor
Scans running processes and checks them against a blacklist of suspicious keywords. If a process name matches something sketchy like "trojan" or "keylogger," it's flagged and logged.

File Monitor
Tracks file changes in a specified directory. Hashes files and checks for modifications between scans. If a file is altered, it's logged as a potential security issue.

Incident Database
Uses SQLite to store all detected security incidents. Keeps track of timestamps and descriptions of threats, allowing for historical analysis.

Alert Manager
Sends alerts via email when a security event is detected. Requires SMTP credentials to send notifications. If credentials are missing, it logs an error instead.

API Server
Runs a Flask-based API that allows retrieval of logged incidents. Provides an endpoint to fetch incident reports in JSON format.

Command Line Interface (CLI)
A basic interactive CLI for checking the system status and manually interacting with the monitoring system.

Running the System
To get this thing rolling, run the main.py script. This will launch the API server, start the CLI, and kick off the monitoring process. The system will continuously scan for threats, analyze logs, track file changes, and store everything in the database.

You’ll need an SMTP server and credentials if you want email alerts. Without those, it’ll still log threats but won’t send out notifications.

Configuration
Most settings are hardcoded, but you can tweak things like the directory for file monitoring, suspicious process keywords, and log patterns by modifying the respective classes. The API server runs on port 5000 by default, but you can change that when starting the server.

Dependencies
You'll need Python and a few libraries installed:

nginx
Copy
Edit
pip install flask psutil sqlite3
Other than that, just make sure you have proper permissions to read system logs, scan files, and monitor processes.

Logs and Data Storage
All logs are stored in logs/system.log. The database file for incidents is in data/incidents.db. If the database doesn’t exist, it’ll be created automatically.

Notes
This is not a replacement for enterprise security tools, but it’s a solid lightweight monitoring system. It’s built to be simple, efficient, and effective at spotting threats in real time. If you need more advanced detection, you’ll probably want to integrate this with a larger security stack.

If you run this on a production system, be aware that network scanning and process monitoring can sometimes trigger security alerts themselves. Use it responsibly.
