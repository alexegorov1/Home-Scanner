import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config_loader import load_config

class AlertManager:
    def __init__(self):
        cfg = load_config()
        smtp_cfg = cfg.get("alerts", {}).get("smtp", {})
        self.email = smtp_cfg.get("user", "admin@example.com")
        self.smtp_server = smtp_cfg.get("server", "smtp.example.com")
        self.smtp_port = smtp_cfg.get("port", 587)
        self.smtp_user = smtp_cfg.get("user")
        self.smtp_password = smtp_cfg.get("password")

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def send_alert(self, threat: str):
        logging.warning(f"ALERT: {threat} detected! Notification sent to {self.email}.")
        self._send_email(threat)

    def _send_email(self, threat: str):
        if not self.smtp_user or not self.smtp_password:
            logging.error("SMTP credentials are not set.")
            return

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = self.email
        msg["Subject"] = f"Security Alert - {threat}"
        msg.attach(MIMEText(
            f"An alert has been triggered:\n\n{threat}\n\nPlease investigate.", "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.email, msg.as_string())
                logging.info(f"Email alert sent to {self.email}")
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")
