import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config_loader import load_config
from socket import gaierror, timeout

class AlertManager:
    def __init__(self):
        cfg = load_config()
        smtp_cfg = cfg.get("alerts", {}).get("smtp", {})
        self.email_to = smtp_cfg.get("to", "alert@example.com")
        self.smtp_server = smtp_cfg.get("server", "smtp.example.com")
        self.smtp_port = smtp_cfg.get("port", 587)
        self.smtp_user = smtp_cfg.get("user", "")
        self.smtp_password = smtp_cfg.get("password", "")
        self.email_from = self.smtp_user or "noreply@example.com"

        self.enabled = all([self.smtp_user, self.smtp_password, self.smtp_server, self.email_to])

        self.logger = logging.getLogger("AlertManager")
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def send_alert(self, threat: str):
        self.logger.warning(f"ALERT: {threat}")
        if not self.enabled:
            self.logger.warning("Email alerts are disabled or misconfigured.")
            return
        self._send_email(threat)

    def _send_email(self, threat: str):
        msg = MIMEMultipart()
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg["Subject"] = f"[Security Alert] {threat}"
        msg.attach(MIMEText(
            f"A security alert has been triggered:\n\n{threat}\n\nCheck logs or take action.", "plain"
        ))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                self.logger.info(f"Alert email sent to {self.email_to}")
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
            self.logger.error(f"SMTP error while sending alert: {e}")
        except (gaierror, timeout) as e:
            self.logger.error(f"Network error while sending alert: {e}")
        except Exception as e:
            self.logger.exception(f"Unexpected error during email alert: {e}")
