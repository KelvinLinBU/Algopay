# algo_pay/notifier.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional


class Notifier:
    """Base notifier interface."""

    def notify(
        self, payload: Dict[str, Any], recipient_override: Optional[str] = None
    ) -> None:
        """Send a notification given a payload."""
        raise NotImplementedError("Subclasses must implement notify()")


class ConsoleNotifier(Notifier):
    """Simple notifier that prints to console."""

    def notify(
        self, payload: Dict[str, Any], recipient_override: Optional[str] = None
    ) -> None:
        print(f"[ConsoleNotifier] Notification: {payload}")


class EmailNotifier(Notifier):
    """
    Notifier that sends emails directly via SMTP.
    Expects SMTP credentials and default recipient info on initialization.
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email

    def notify(
        self, payload: Dict[str, Any], recipient_override: Optional[str] = None
    ) -> None:
        """Send an email immediately with job details in the payload."""
        recipient = recipient_override or self.recipient_email

        subject = f"Payroll Job Completed: {payload.get('job_id', 'UnknownJob')}"
        body = (
            f"Payroll Job ID: {payload.get('job_id', 'N/A')}\n"
            f"Department: {payload.get('department', 'N/A')}\n"
            f"Employees Paid: {payload.get('employees', [])}\n"
            f"Transaction IDs: {payload.get('txids', [])}\n"
            f"Status: {payload.get('status', 'Unknown')}\n"
        )

        # Build email message
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, message.as_string())
            print(
                f"[EmailNotifier] Email sent to {recipient} for job {payload.get('job_id')}"
            )
        except Exception as e:
            print(f"[EmailNotifier] Failed to send email: {e}")
