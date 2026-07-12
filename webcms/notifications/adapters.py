"""
Email adapters for SMTP and SendGrid.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod


class EmailAdapter(ABC):
    """Base email adapter."""

    @abstractmethod
    async def send(self, to_email, subject, html_body, text_body=None, from_email=None):
        pass


class SMTPAdapter(EmailAdapter):
    """SMTP email adapter."""

    def __init__(self, host="localhost", port=587, username=None,
                 password=None, use_tls=True, from_email="noreply@webcms.local"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_email = from_email

    async def send(self, to_email, subject, html_body, text_body=None, from_email=None):
        """Send email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email or self.from_email
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(msg["From"], [to_email], msg.as_string())
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SendGridAdapter(EmailAdapter):
    """SendGrid email adapter."""

    def __init__(self, api_key, from_email="noreply@webcms.local"):
        self.api_key = api_key
        self.from_email = from_email

    async def send(self, to_email, subject, html_body, text_body=None, from_email=None):
        """Send email via SendGrid API."""
        try:
            import urllib.request
            import json

            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email or self.from_email},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text_body or ""},
                    {"type": "text/html", "value": html_body}
                ]
            }

            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=json.dumps(data).encode(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            urllib.request.urlopen(req)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
