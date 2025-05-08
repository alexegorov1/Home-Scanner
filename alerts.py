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
        smtp_cfg = cfg.get("alerts", {}).get("smtp", {})

        self.email_to = smtp_cfg.get("to", "")
        self.smtp_server = smtp_cfg.get("server", "")
        self.smtp_port = smtp_cfg.get("port", 587)
        self.smtp_user = smtp_cfg.get("user", "")
        self.smtp_password = smtp_cfg.get("password", "")
        self.email_from = self.smtp_user or "noreply@example.com"
        self.use_tls = smtp_cfg.get("use_tls", True)

        self.enabled = all((self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password, self.email_to))

        self.logger = logging.getLogger("AlertManager")
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def send_alert(self, message, severity="warning", source="homescanner"):
        if not message:
            self.logger.error("Empty alert message, skipping.")
            return

        entry = f"[{severity.upper()}] {source} - {message}"
        self.logger.warning(entry)

        if not self.enabled:
            self.logger.warning("Alert not sent: SMTP configuration incomplete.")
            return

        self._send_email_alert(f"[{severity.upper()}] {source}", message)

    def _send_email_alert(self, subject, body):
        msg = MIMEMultipart()
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg["Subject"] = subject
        msg.attach(MIMEText(
            f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n{body}\n\nPlease investigate.", "plain"
        ))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                self.logger.info(f"Alert email sent to {self.email_to}")
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException, gaierror, timeout, Exception) as e:
            self.logger.error(f"Failed to send alert email: {e}")
