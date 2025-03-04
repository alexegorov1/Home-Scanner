import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertManager:
    def __init__(self, email="security@sentinelguard.com", smtp_server="smtp.example.com", smtp_port=587, smtp_user=None, smtp_password=None):
        self.email = email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def send_alert(self, threat):
        logging.warning(f"ALERT: {threat} detected! Notification sent to {self.email}.")
        self.send_email_notification(threat)
    
    def send_email_notification(self, threat):
        if not self.smtp_user or not self.smtp_password:
            logging.error("SMTP credentials are not set. Email notification cannot be sent.")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.email
            msg['Subject'] = f"Security Alert - {threat}"
            
            body = f"An alert has been triggered due to the detection of: {threat}. Please take necessary actions."
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.email, msg.as_string())
            
            logging.info(f"Email successfully sent to {self.email}.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
