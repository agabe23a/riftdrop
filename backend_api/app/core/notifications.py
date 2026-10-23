import asyncio
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException

from app.core.config import settings


async def send_email(recipient: str, subject: str, body: str) -> None:
    """Send transactional email through a configured SMTP relay."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=503, detail="Account notifications are not configured")
        return

    def deliver():
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as client:
            if settings.SMTP_STARTTLS:
                client.starttls()
            if settings.SMTP_USERNAME:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
            client.send_message(message)

    try:
        await asyncio.to_thread(deliver)
    except (OSError, smtplib.SMTPException) as error:
        raise HTTPException(status_code=502, detail="Unable to deliver account notification") from error
