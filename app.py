from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import uuid

from database import init_db, get_db
from models import EmailLog, ScheduledEmail
from email_sender import send_email
from scheduler import start_scheduler

# Load .env
load_dotenv()

app = Flask(__name__)

# Allow frontend access (update origins if needed)
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5000").split(",")
CORS(app, resources={
    r"/*": {
        "origins": [o.strip() for o in allowed_origins if o.strip()],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize database and start background scheduler
# init_db()
# start_scheduler()


@app.get("/health")
def health():
    """Check if the service is running."""
    return jsonify({"status": "ok", "service": "email-microservice"}), 200

def _normalize_recipients(raw):
    """
    Normalize recipients:
    - must be a list
    - trim spaces
    - lowercase
    - drop empty
    - de-duplicate (preserve order)
    """
    if not isinstance(raw, list):
        return None
    cleaned = []
    seen = set()
    for r in raw:
        if isinstance(r, str):
            v = r.strip().lower()
            if v and v not in seen:
                seen.add(v)
                cleaned.append(v)
    return cleaned


def _validate_lengths(subject_line: str, body: str):
    """
    Light input guardrails to keep logs and payloads reasonable.
    Adjust limits as needed.
    """
    MAX_SUBJECT = 256
    MAX_BODY = 100_000
    if len(subject_line) > MAX_SUBJECT:
        return False, f"'subject_line' too long (>{MAX_SUBJECT})"
    if len(body) > MAX_BODY:
        return False, f"'body' too long (>{MAX_BODY} chars)"
    return True, ""

@app.post("/send-email")
def send_email_endpoint():
    """
    Send a basic email.
    Request JSON:
    {
      "program_key": "string",
      "recipients": ["email1@example.com"],   # prefer this key
      "recipiants": ["email1@example.com"],   # typo supported
      "subject_line": "string",
      "body": "string",
      "is_html": boolean
    }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}

        # Read user input
        program_key = data.get("program_key", "")
        used_legacy = "recipiants" in data and "recipients" not in data
        recipients_raw = data.get("recipients", data.get("recipiants", []))
        subject_line = data.get("subject_line", "")
        body = data.get("body", "")
        is_html = bool(data.get("is_html", False))

        # Normalize recipients
        recipients = _normalize_recipients(recipients_raw)
        if recipients is None:
            return jsonify({"status": "failed", "message": "Invalid 'recipients'", "statusCode": 400}), 400
        if not recipients:
            return jsonify({"status": "failed", "message": "Empty 'recipients'", "statusCode": 400}), 400

        # Optional confirmation copy to owner
        confirm_to = os.getenv("CONFIRMATION_TO")
        if confirm_to:
            ct = confirm_to.strip().lower()
            if ct and ct not in recipients:
                recipients.append(ct)

        # Required fields
        if not program_key:
            return jsonify({"status": "failed", "message": "Missing 'program_key'", "statusCode": 400}), 400
        if not subject_line:
            return jsonify({"status": "failed", "message": "Missing 'subject_line'", "statusCode": 400}), 400
        if not body:
            return jsonify({"status": "failed", "message": "Missing 'body'", "statusCode": 400}), 400

        # Length guardrails
        ok, reason = _validate_lengths(subject_line, body)
        if not ok:
            return jsonify({"status": "failed", "message": reason, "statusCode": 400}), 400

        # Send
        success, status_code, message = send_email(recipients, subject_line, body, is_html)

        # Log
        db = get_db()
        try:
            log = EmailLog(
                program_key=program_key,
                recipients=",".join(recipients),
                subject_line=subject_line,
                body=body,
                is_html=is_html,
                status="sent" if success else "failed",
                status_code=status_code,
                sent_at=datetime.now(timezone.utc) if success else None,
            )
            db.add(log)
            db.commit()
        finally:
            db.close()

        # Response
        payload = {
            "status": "success" if success else "failed",
            "message": "Email sent successfully" if success else message,
            "details": {"recipients": recipients, "subject_line": subject_line} if success else None,
            "statusCode": 200 if success else status_code
        }
        if used_legacy:
            payload["hint"] = "Use 'recipients' instead of legacy 'recipiants'."
        return jsonify(payload), (200 if success else status_code)

    except Exception as e:
        print(f"[send-email] error: {e}")
        return jsonify({"status": "failed", "message": "Server error", "statusCode": 500}), 500


@app.post("/send-timed-email")
def send_timed_email_endpoint():
    """
    Create a scheduled email to send later.
    Request JSON:
    {
      "program_key": "string",
      "recipients": ["email@example.com"],     # prefer this key
      "recipiants": ["email@example.com"],     # legacy key supported
      "subject_line": "string",
      "body": "string",
      "is_html": boolean,
      "time_to_send": "HH:MM",                 # e.g., "14:30"
      "date_to_send": "YYYY-MM-DD"             # e.g., "2025-11-15"
    }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}

        program_key = data.get("program_key", "")
        used_legacy = "recipiants" in data and "recipients" not in data
        recipients_raw = data.get("recipients", data.get("recipiants", []))
        subject_line = data.get("subject_line", "")
        body = data.get("body", "")
        is_html = bool(data.get("is_html", False))
        time_to_send = data.get("time_to_send", "")
        date_to_send = data.get("date_to_send", "")

        # Presence check
        if not all([program_key, recipients_raw, subject_line, body, time_to_send, date_to_send]):
            return jsonify({"status": "failed", "message": "Missing required fields", "statusCode": 400}), 400

        # Normalize recipients
        recipients = _normalize_recipients(recipients_raw)
        if recipients is None:
            return jsonify({"status": "failed", "message": "Invalid 'recipients'", "statusCode": 400}), 400
        if not recipients:
            return jsonify({"status": "failed", "message": "Empty 'recipients'", "statusCode": 400}), 400

        # Length guardrails
        ok, reason = _validate_lengths(subject_line, body)
        if not ok:
            return jsonify({"status": "failed", "message": reason, "statusCode": 400}), 400

        # Combine date+time → UTC aware
        try:
            scheduled_dt = datetime.strptime(f"{date_to_send} {time_to_send}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            return jsonify({"status": "failed", "message": "Invalid date or time format", "statusCode": 400}), 400

        if scheduled_dt <= datetime.now(timezone.utc):
            return jsonify({"status": "failed", "message": "Scheduled time must be in the future", "statusCode": 400}), 400

        # Create id and persist
        schedule_id = uuid.uuid4().hex
        db = get_db()
        try:
            scheduled_email = ScheduledEmail(
                schedule_id=schedule_id,
                program_key=program_key,
                recipients=",".join(recipients),
                subject_line=subject_line,
                body=body,
                is_html=is_html,
                scheduled_time=scheduled_dt,
                status="scheduled",
            )
            db.add(scheduled_email)
            db.commit()
            try:
                confirm_to = os.getenv("CONFIRMATION_TO", "").strip().lower()
                if confirm_to:
                    confirm_subject = f"[EmailService] Complete your appointment! - {schedule_id}"
                    confirm_body = f"""
                    <html><body>
                      <h3>Your appointment has been successfully created</h3>
                      <ul>
                        <li><b>Schedule ID:</b> {schedule_id}</li>
                        <li><b>Recipients:</b> {", ".join(recipients)}</li>
                        <li><b>Subject:</b> {subject_line}</li>
                        <li><b>Send at (UTC):</b> {scheduled_dt.isoformat()}</li>
                      </ul>
                    </body></html>
                    """
                    c_success, c_code, c_msg = send_email([confirm_to], confirm_subject, confirm_body, is_html=True)

                    # Check email log
                    clog = EmailLog(
                        program_key=program_key,
                        recipients=confirm_to,
                        subject_line=confirm_subject,
                        body=confirm_body,
                        is_html=True,
                        status="sent" if c_success else "failed",
                        status_code=c_code,
                        sent_at=datetime.now(timezone.utc) if c_success else None,
                    )
                    db.add(clog)
                    db.commit()
            except Exception as ce:
                print(f"[send-timed-email] confirmation error: {ce}")

        finally:
            db.close()

        payload = {
            "status": "success",
            "message": "Timed email created successfully",
            "details": {
                "schedule_id": schedule_id,
                "recipients": recipients,
                "subject_line": subject_line,
                "time_to_send": time_to_send,
                "date_to_send": date_to_send
            },
            "statusCode": 201
        }
        if used_legacy:
            payload["hint"] = "Use 'recipients' instead of legacy 'recipiants'."
        return jsonify(payload), 201

    except Exception as e:
        print(f"[send-timed-email] error: {e}")
        return jsonify({"status": "failed", "message": "Failed to schedule email", "statusCode": 500}), 500


@app.get("/check-scheduled-email/<schedule_id>")
def check_scheduled_email(schedule_id: str):
    """Return the status of a scheduled email, or 404 if not found."""
    try:
        db = get_db()
        try:
            email = db.query(ScheduledEmail).filter(
                ScheduledEmail.schedule_id == schedule_id
            ).first()
        finally:
            db.close()

        if not email:
            return jsonify({"status": "failed", "message": "Schedule ID not found", "statusCode": 404}), 404

        return jsonify({
            "status": "success",
            "email_status": email.status,
            "scheduled_time": email.scheduled_time.isoformat(),
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "statusCode": 200
        }), 200

    except Exception as e:
        print(f"[check-scheduled-email] error: {e}")
        return jsonify({"status": "failed", "message": "Error checking email status", "statusCode": 500}), 500


if __name__ == "__main__":
    # Init DB and start background scheduler only when running the app directly
    init_db()
    start_scheduler()
    port = int(os.getenv("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
