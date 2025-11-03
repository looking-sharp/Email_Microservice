import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv  # pip install python-dotenv

# Load .env
load_dotenv()

email = os.getenv("EMAIL")
password = os.getenv("SMTP_PASS")  # Gmail app password
smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))

def send_test_email():
    msg = EmailMessage()
    msg["Subject"] = "This is a test message"
    msg["From"] = email
    msg["To"] = "choio@oregonstate.edu"
    body = "Hi, this is a test message."

    # HTML context
    msg.add_alternative(f"""
        <html><body><p>{body}</p></body></html>
    """, subtype="html")

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.set_debuglevel(1)  # Return SMTP log 
    try:
        server.ehlo()
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        print("Email sent successfully!")
    finally:
        server.quit()

if __name__ == "__main__":
    send_test_email()
