"""Email service for sending verification and password reset emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """Send an email. Returns True on success, False on failure."""
    if not settings.smtp_user or not settings.smtp_password:
        # Log email content in development when SMTP is not configured
        logger.warning(
            f"SMTP not configured. Would send email to {to_email}:\n"
            f"Subject: {subject}\n"
            f"Content: {text_content or html_content[:500]}"
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add text and HTML parts
        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Connect and send
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)

        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, to_email, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_verification_email(to_email: str, token: str, user_name: str) -> bool:
    """Send email verification email."""
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"

    subject = "Verify your email - Life Curriculum Assistant"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Life Curriculum Assistant!</h1>
            <p>Hi {user_name},</p>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
            <p>This link will expire in {settings.email_verification_expire_hours} hours.</p>
            <div class="footer">
                <p>If you didn't create an account, you can safely ignore this email.</p>
                <p>&copy; Life Curriculum Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to Life Curriculum Assistant!

    Hi {user_name},

    Thank you for signing up! Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in {settings.email_verification_expire_hours} hours.

    If you didn't create an account, you can safely ignore this email.
    """

    return await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, token: str, user_name: str) -> bool:
    """Send password reset email."""
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    subject = "Reset your password - Life Curriculum Assistant"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            .warning {{ background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 12px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Reset Your Password</h1>
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password. Click the button below to choose a new password:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #4F46E5;">{reset_url}</p>
            <div class="warning">
                <strong>This link will expire in {settings.password_reset_expire_hours} hour(s).</strong>
            </div>
            <div class="footer">
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                <p>&copy; Life Curriculum Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Reset Your Password

    Hi {user_name},

    We received a request to reset your password. Click the link below to choose a new password:

    {reset_url}

    This link will expire in {settings.password_reset_expire_hours} hour(s).

    If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
    """

    return await send_email(to_email, subject, html_content, text_content)
