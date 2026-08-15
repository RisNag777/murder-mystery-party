"""Optional SMTP email for announcement blasts."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(
        os.getenv("SMTP_HOST")
        and os.getenv("SMTP_FROM")
        and os.getenv("SMTP_USER")
        and os.getenv("SMTP_PASSWORD")
    )


def send_announcement_email(
    *,
    subject: str,
    body: str,
    recipients: list[str],
) -> tuple[bool, str]:
    """Send announcement email to recipients. Returns (ok, message)."""
    if not recipients:
        return False, "No guest email addresses to send to."

    if not smtp_configured():
        return (
            False,
            "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, "
            "SMTP_PASSWORD, and SMTP_FROM in .env — announcement was still saved in-app.",
        )

    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    from_addr = os.environ["SMTP_FROM"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = from_addr
    msg["Bcc"] = ", ".join(recipients)
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True, f"Emailed {len(recipients)} guest(s)."
    except Exception as exc:  # noqa: BLE001 — surface any SMTP failure to host UI
        return False, f"Email failed: {exc}"
