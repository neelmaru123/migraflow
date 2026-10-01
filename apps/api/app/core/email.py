"""
Transactional Email Service for Migraflow (Google Gmail SMTP)
"""

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_smtp_email_sync(
    to_email: str,
    subject: str,
    html_content: str,
    plain_text_content: Optional[str] = None,
) -> bool:
    """Synchronous SMTP email dispatcher executed in thread worker."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP_USER or SMTP_PASSWORD is not configured in environment. "
            f"Password reset email to {to_email} will NOT be sent."
        )
        return False

    sender_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    sender_name = settings.EMAILS_FROM_NAME or "Migraflow Platform"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email

    if plain_text_content:
        msg.attach(MIMEText(plain_text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(sender_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Password reset email successfully sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email} via Google SMTP: {exc}")
        return False


async def send_password_reset_email(
    to_email: str,
    reset_token: str,
    user_name: Optional[str] = None,
) -> bool:
    """
    Format and dispatch password reset email with 5-minute expiration notice.
    """
    name = user_name or to_email.split("@")[0]
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset Your Migraflow Password"

    plain_text = f"""Hello {name},

We received a request to reset your password for your Migraflow account.
Please visit the link below to choose a new password:

{reset_url}

IMPORTANT: This link will expire in 5 minutes.
If you did not request a password reset, please ignore this email.

Best regards,
The Migraflow Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Reset Your Migraflow Password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #09090b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f4f4f5;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #09090b; padding: 40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 540px; background-color: #121215; border: 1px solid #27272a; padding: 36px;">
          <!-- Logo & Brand Header -->
          <tr>
            <td style="padding-bottom: 24px; border-bottom: 1px solid #27272a;">
              <table role="presentation" width="100%">
                <tr>
                  <td>
                    <span style="font-size: 18px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; text-transform: uppercase;">
                      MIGRA<span style="color: #38bdf8;">FLOW</span>
                    </span>
                  </td>
                  <td align="right">
                    <span style="font-size: 11px; font-family: monospace; color: #38bdf8; background-color: #0c1824; border: 1px solid rgba(56, 189, 248, 0.3); padding: 4px 8px; text-transform: uppercase;">
                      Security Notification
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding-top: 28px; padding-bottom: 20px;">
              <h1 style="font-size: 20px; font-weight: 700; color: #ffffff; margin: 0 0 12px 0;">
                Password Reset Request
              </h1>
              <p style="font-size: 14px; line-height: 1.6; color: #a1a1aa; margin: 0 0 18px 0;">
                Hello <strong style="color: #ffffff;">{name}</strong>,
              </p>
              <p style="font-size: 14px; line-height: 1.6; color: #a1a1aa; margin: 0 0 24px 0;">
                We received a request to reset your password for your Migraflow account. Click the button below to set a new password:
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
                <tr>
                  <td style="background-color: #38bdf8;">
                    <a href="{reset_url}" target="_blank" style="display: inline-block; padding: 12px 28px; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; color: #000000; text-decoration: none; text-transform: uppercase;">
                      Reset Password &rarr;
                    </a>
                  </td>
                </tr>
              </table>

              <!-- 5-Min Expiry Alert Box -->
              <div style="background-color: #18181b; border-left: 3px solid #f59e0b; padding: 12px 16px; margin-bottom: 24px;">
                <p style="font-size: 12px; font-family: monospace; color: #fbbf24; margin: 0;">
                  &#9888; <strong>ATTENTION:</strong> This link will expire in <strong>5 minutes</strong>.
                </p>
              </div>

              <!-- Fallback Direct URL -->
              <p style="font-size: 12px; color: #71717a; line-height: 1.5; margin: 0 0 8px 0;">
                If the button above doesn't work, copy and paste this URL into your browser:
              </p>
              <p style="font-size: 11px; font-family: monospace; color: #38bdf8; word-break: break-all; margin: 0 0 24px 0; background-color: #09090b; padding: 10px; border: 1px solid #27272a;">
                {reset_url}
              </p>

              <p style="font-size: 12px; color: #71717a; line-height: 1.5; margin: 0;">
                If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding-top: 24px; border-top: 1px solid #27272a; text-align: center;">
              <p style="font-size: 11px; font-family: monospace; color: #52525b; margin: 0;">
                &copy; Migraflow Platform &bull; Automated Data Migration Engine
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    return await asyncio.to_thread(
        _send_smtp_email_sync,
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        plain_text_content=plain_text,
    )
