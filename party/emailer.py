"""Optional SMTP email for announcement blasts."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from party.settings import get_setting


def smtp_configured() -> bool:
    return bool(
        get_setting("SMTP_HOST")
        and get_setting("SMTP_FROM")
        and get_setting("SMTP_USER")
        and get_setting("SMTP_PASSWORD")
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
            "SMTP is not configured. Set SMTP_* in .env (local) or Streamlit Secrets "
            "(Cloud) — announcement was still saved in-app.",
        )

    host = get_setting("SMTP_HOST")
    port = int(get_setting("SMTP_PORT", "587") or "587")
    user = get_setting("SMTP_USER")
    password = get_setting("SMTP_PASSWORD")
    from_addr = get_setting("SMTP_FROM")

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
