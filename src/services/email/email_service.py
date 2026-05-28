import os
import smtplib
import logging
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotificationService:
    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("ALERT_EMAIL_FROM")
        self.email_to = os.getenv("ALERT_EMAIL_TO")
        
    def send_email(
        self,
        subject: str,
        body: str,
    ) -> dict:
        try:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = self.email_from
            message["To"] = self.email_to
            message.set_content(body)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info("Inventory alert email sent successfully")
            return {
                "status": "success",
                "message": "Email sent successfully.",
            }
        
        except Exception:
            logger.exception("Failed to send inventory alert email.")
            return {
                "status": "error",
                "message": "Failed to send email.",
            }
        
        