"""Email sending via SMTP (e.g. Gmail).

Uses stdlib smtplib in a thread (STARTTLS). For Gmail, ``SMTP_PASSWORD`` must be a
16-character **App Password** (generated at https://myaccount.google.com/apppasswords),
not the normal account password — and 2-Step Verification must be enabled.
"""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)


def _send_sync(settings: Settings, to: str, subject: str, text: str, html: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls(context=context)
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_email(settings: Settings, to: str, subject: str, text: str, html: str) -> None:
    await asyncio.to_thread(_send_sync, settings, to, subject, text, html)


async def send_verification_email(settings: Settings, to: str, link: str) -> None:
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:480px;margin:auto">
      <h2 style="margin-bottom:4px">Verify your FinSight account</h2>
      <p style="color:#555">Confirm your email address to finish signing up.</p>
      <p style="margin:24px 0">
        <a href="{link}" style="background:#4f46e5;color:#fff;padding:10px 18px;
           border-radius:8px;text-decoration:none">Verify email</a>
      </p>
      <p style="color:#888;font-size:13px">Or paste this link: {link}</p>
    </div>
    """
    await send_email(
        settings,
        to,
        "Verify your FinSight account",
        f"Verify your FinSight account: {link}",
        html,
    )
