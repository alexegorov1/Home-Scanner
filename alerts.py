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

        self.email_to = smtp_cfg.get("to", "alert@example.com")
        self.smtp_server = smtp_cfg.get("server", "smtp.example.com")
        self.smtp_port = smtp_cfg.get("port", 587)
        self.smtp_user = smtp_cfg.get("user", "")
        self.smtp_password = smtp_cfg.get("password", "")
        self.email_from = self.smtp_user or "noreply@example.com"
        self.use_tls = smtp_cfg.get("use_tls", True)

        self.enabled = all([
            self.smtp_server, self.smtp_port,
            self.smtp_user, self.smtp_password,
            self.email_to
        ])

        self.logger = logging.getLogger("AlertManager")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def send_alert(self, message, severity="warning", source="homescanner"):
        if not message:
            self.logger.error("Alert message is empty, skipping alert.")
            return

        log_entry = f"[{severity.upper()}] {source} - {message}"
        self.logger.warning(log_entry)

        if not self.enabled:
            self.logger.warning("Email alert not sent: email configuration is incomplete or disabled.")
            return

        self._send_email_alert(subject=f"[{severity.upper()}] {source}", body=message)

    def _send_email_alert(self, subject, body):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        msg = MIMEMultipart()
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg["Subject"] = subject
        msg.attach(MIMEText(
            f"Timestamp: {timestamp}\n\n{body}\n\nCheck system logs or take further action if needed.", "plain"
        ))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                self.logger.info(f"Alert email sent to {self.email_to}")
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error during alert delivery: {e}")
        except (gaierror, timeout) as e:
            self.logger.error(f"Network error during SMTP session: {e}")
        except Exception as e:
            self.logger.exception(f"Unexpected exception while sending alert: {e}")
