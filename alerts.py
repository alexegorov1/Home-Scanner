import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config_loader import load_config
from socket import gaierror, timeout
from datetime import datetime

class AlertManager:
    def __init__(self):
        cfg = load_config()
        smtp = cfg.get("alerts", {}).get("smtp", {})

        self.email_to = smtp.get("to", "")
        self.email_from = smtp.get("user", "") or "noreply@example.com"
        self.smtp_server = smtp.get("server", "")
        self.smtp_port = smtp.get("port", 587)
        self.smtp_user = smtp.get("user", "")
        self.smtp_password = smtp.get("password", "")
        self.use_tls = smtp.get("use_tls", True)

        self.enabled = all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password, self.email_to])

        self.logger = logging.getLogger("AlertManager")
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def send_alert(self, message, severity="warning", source="homescanner"):
        if not message:
            self.logger.error("Skipped sending alert: message was empty.")
            return

        entry = f"[{severity.upper()}] {source} - {message}"
        self.logger.warning(entry)

        if not self.enabled:
            self.logger.warning("Skipped sending alert: SMTP config incomplete or disabled.")
            return

        self._send_email(f"[{severity.upper()}] {source}", message)
