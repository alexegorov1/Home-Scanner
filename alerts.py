import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class AlertManager:
    DEFAULT_EMAIL = "{recipient}@sentinelguard.com"
    DEFAULT_SMTP_SERVER = "smtp.example.com"
    DEFAULT_SMTP_PORT = 587

    def __init__(self, recipient: str, smtp_server: str = DEFAULT_SMTP_SERVER,
                 smtp_port: int = DEFAULT_SMTP_PORT, smtp_user: Optional[str] = None,
                 smtp_password: Optional[str] = None) -> None:
        self.email = self.DEFAULT_EMAIL.format(recipient=recipient)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def send_alert(self, threat: str) -> None:
        logging.warning(f"ALERT: {threat} detected! Notification sent to {self.email}.")
        self.send_email_notification(threat)

    def send_email_notification(self, threat: str) -> None:
        if not self.smtp_user or not self.smtp_password:
            logging.error("SMTP credentials are not set. Email notification cannot be sent.")
            return

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = self.email
        msg["Subject"] = f"Security Alert - {threat}"
        msg.attach(MIMEText(f"An alert has been triggered due to the detection of: {threat}. Please take necessary actions.", "plain"))

        server = None
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, self.email, msg.as_string())
            logging.info(f"Email successfully sent to {self.email}.")
        except smtplib.SMTPException as e:
            logging.error(f"Failed to send email due to SMTP error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while sending email: {e}")
        finally:
            if server:
                server.quit()
