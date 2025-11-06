import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", user or "noreply@example.com")
    use_tls = os.getenv("SMTP_USE_TLS", "1") == "1"
    use_ssl = os.getenv("SMTP_USE_SSL", "0") == "1" or port == 465
    login_disabled = os.getenv("SMTP_LOGIN_DISABLED", "0") == "1"

    if not host:
        print("[email] Missing SMTP_HOST")
        return False
    if not login_disabled and (not user or not password):
        print("[email] Missing SMTP_USER/SMTP_PASSWORD (or set SMTP_LOGIN_DISABLED=1)")
        return False


def build_review_invite_email(employee_name: str, link: str, base_url: str, supervisor_link: str = None) -> str:
    logo_url = f"{base_url.rstrip('/')}/static/logo.png"
    days = int(os.getenv('MAGIC_LINK_MAX_AGE_SECONDS', '604800')) // 86400
    extra_supervisor = (
        f"""
            <tr>
              <td style=\"padding:0 24px 12px 24px;color:#374151;font-size:14px;line-height:1.6;\">
                <p style=\"margin:0 0 8px 0;\"><strong>Are you a supervisor?</strong> You can also review your team using the link below:</p>
              </td>
            </tr>
            <tr>
              <td align=\"center\" style=\"padding:0 24px 20px 24px;\">
                <a href=\"{supervisor_link}\" style=\"background:#16a34a;color:#ffffff;text-decoration:none;padding:10px 16px;border-radius:8px;display:inline-block;font-weight:600;\">Open supervisor dashboard</a>
              </td>
            </tr>
        """
    ) if supervisor_link else ""

    return (
        f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f8fafc;font-family:Segoe UI, Roboto, Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;">
      <tr>
        <td align="center" style="padding:24px;">
          <table role="presentation" width="640" cellspacing="0" cellpadding="0" style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
            <tr>
              <td align="center" style="padding:24px 24px 0 24px;">
                <img src="{logo_url}" alt="Company Logo" style="max-width:200px;height:auto;display:block;">
              </td>
            </tr>
            <tr>
              <td style="padding:16px 24px 0 24px;">
                <h1 style="margin:0;color:#111827;font-size:22px;">Employee Review Notice</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:12px 24px;color:#374151;font-size:14px;line-height:1.6;">
                <p style="margin:0 0 12px 0;">Hi {employee_name.split(' ')[0] if employee_name else 'there'},</p>
                <p style="margin:0 0 12px 0;">We’re excited to launch our employee reviews. These are designed to be positive, supportive, and constructive.</p>
                <p style="margin:0 0 8px 0;">What these reviews are for:</p>
                <ul style="margin:0 0 12px 18px;padding:0;">
                  <li>Hearing how you’re feeling in your role</li>
                  <li>Providing an open space for honest feedback</li>
                  <li>Reflecting on goals, growth, and accomplishments</li>
                  <li>Identifying how we can support your development</li>
                </ul>
                <p style="margin:0 0 12px 0;">Please complete your review within the next two weeks. Your responses are confidential and intended to help you thrive.</p>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:4px 24px 20px 24px;">
                <a href="{link}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:8px;display:inline-block;font-weight:600;">Open your review</a>
                <div style="color:#6b7280;font-size:12px;margin-top:10px;">If the button doesn’t work, copy this URL:<br>{link}</div>
                <div style="color:#9ca3af;font-size:12px;margin-top:8px;">This secure link expires in {days} days.</div>
              </td>
            </tr>
            {extra_supervisor}
            <tr>
              <td style="padding:0 24px 20px 24px;color:#374151;font-size:14px;line-height:1.6;">
                <p style="margin:0;">Thank you,<br>Mack Kirk Roofing Leadership Team</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
  </html>
"""
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if not login_disabled:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                if not login_disabled:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[email] Send failed: {e}")
        return False


def send_email_verbose(to_email: str, subject: str, html_body: str):
    """Send email and return (ok: bool, error: str | None)."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", user or "noreply@example.com")
    use_tls = os.getenv("SMTP_USE_TLS", "1") == "1"
    use_ssl = os.getenv("SMTP_USE_SSL", "0") == "1" or port == 465
    login_disabled = os.getenv("SMTP_LOGIN_DISABLED", "0") == "1"

    if not host:
        return False, "Missing SMTP_HOST"
    if not login_disabled and (not user or not password):
        return False, "Missing SMTP_USER/SMTP_PASSWORD (or set SMTP_LOGIN_DISABLED=1)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if not login_disabled:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                if not login_disabled:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


