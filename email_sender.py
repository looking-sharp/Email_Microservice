import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def send_email(recipients: list, subject: str, body: str, is_html: bool = False) -> tuple[bool, int, str]:
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL
        msg['To'] = ', '.join([r.strip() for r in recipients if r and r.strip()])

        if is_html:
            msg.add_alternative(body, subtype="html")
        else:
            msg.add_alternative(f"<html><body><pre style='white-space: pre-wrap'>{body}</pre></body></html>", subtype="html")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL, SMTP_PASS)
            server.send_message(msg)

        return True, 200, "Email sent successfully"

    except smtplib.SMTPAuthenticationError as e:
        return False, 401, f"SMTP auth failed: {e}"
    except smtplib.SMTPConnectError as e:
        return False, 503, f"SMTP connection failed: {e}"
    except smtplib.SMTPException as e:
        return False, 500, f"SMTP error: {e}"
    except Exception as e:
        return False, 520, f"Unknown error: {e}"
