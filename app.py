from flask import Flask, jsonify, redirect, url_for, render_template, request 
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
from datetime import datetime, timezone
import uuid
import json

from database import init_db, get_db, save_email_log, save_scheduled_email, find_in_db
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

def _normalize_recipients(raw: list[str]):
    """ Returns a cleaned list of recipiants from an email request.
        (Trims spaces, makes lowercase, removes duplicated / empty)
    
    Args:
        raw (list[str]): Inputted list of emails 
    
    Returns:
        list[str]: the cleaned version of the raw list
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
    """ Light input guardrails to keep logs and payloads reasonable.
        Limites can be adjusted as needed.

    Args:
        subject_line (str): subject line of the email
        body (str): body of the email
    
    Returns:
        Boolean: If the subject line and body are smaller than max
        str: Error message for if it's too large
    """
    MAX_SUBJECT = 256
    MAX_BODY = 100_000
    if len(subject_line) > MAX_SUBJECT:
        return False, f"'subject_line' too long (>{MAX_SUBJECT})"
    if len(body) > MAX_BODY:
        return False, f"'body' too long (>{MAX_BODY} chars)"
    return True, ""

# ------------------------
#   API CALLS
# ------------------------

@app.get("/health")
def health():
    """Check if the service is running."""
    return jsonify({"status": "ok", "service": "email-microservice"}), 200


@app.post("/send-email")
def send_email_endpoint():
    """ HTTP Request that takes in an JSON package and sends
        an email with the data from that package.

    Args:
        Request (JSON):
            {
            "recipients": ["string],            # list of recipiant emails
            "recipiants": ["string"],           # typo supported
            "subject_line": "string",           # subject line of email
            "body": "string",                   # body of email
            "is_html": boolean                  # if body is formatted as HTML
            }
    
    Returns:
        JSON:
            {
            "status": "string",                 # "success" or "failed"
            "message": "string",                # Outcome of the email process
            "statusCode": Integer,              # The status code of the email
            "details": ["string"], "string"     # the subject line and recipiants of the email if success
            }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        # Read user input
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
        with get_db() as db:
            save_email_log(db, recipients, subject_line, body, is_html, success, status_code)

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
    """ HTTP Request that takes in an JSON package and submits 
        a request to send an email with the provided data at a 
        later time and or date

    Args:
        Request (JSON):
            {
            "recipients": ["string],            # list of recipiant emails
            "recipiants": ["string"],           # typo supported
            "subject_line": "string",           # subject line of email
            "body": "string",                   # body of email
            "is_html": boolean,                 # if body is formatted as HTML
            "time_to_send": "string",           # formatted as "HH:MM" (24 hour UTC)
            "date_to_send": "string"            # formatted as "YYYY-MM-DD"
            }
    
    Returns:
        JSON:
            {
            "status": "string",                 # "success" or "failed"
            "message": "string",                # Outcome of the email process
            "statusCode": Integer,              # The status code of the email
            "details":                          # if success, return details of scheduled email
                {
                "schedule_id": "string",
                "recipients": ["string"],
                "subject_line": "string",
                "time_to_send": "string",
                "date_to_send": "string"
                }
            }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}

        used_legacy = "recipiants" in data and "recipients" not in data
        recipients_raw = data.get("recipients", data.get("recipiants", []))
        subject_line = data.get("subject_line", "")
        body = data.get("body", "")
        is_html = bool(data.get("is_html", False))
        time_to_send = data.get("time_to_send", "")
        date_to_send = data.get("date_to_send", "")

        # Presence check
        if not all([recipients_raw, subject_line, body, time_to_send, date_to_send]):
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
        with get_db() as db:
            # Save scheduled email
            scheduled_ok = save_scheduled_email(db, schedule_id, recipients, subject_line, body, is_html, scheduled_dt)
            if not scheduled_ok:
                print("[send-timed-email] Failed to save scheduled email")
            else:
                confirm_to = os.getenv("CONFIRMATION_TO", "").strip().lower()
                if confirm_to:
                    try:
                        c_subject_line = f"[EmailService] Complete your appointment! - {schedule_id}"
                        c_body = f""" 
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
                        c_success, c_code, c_msg = send_email([confirm_to], c_subject_line, c_body, is_html=True)
                        
                        # Log
                        save_email_log(db, [confirm_to], c_subject_line, c_body, True, c_success, c_code)
                    except Exception as e:
                        print(f"[send-timed-email] Confirmation error: {e}")
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
    """Return the status of a scheduled email, or 404 if not found.
    
    Args:
        schedule_id (string): the schedule id of the email
    
    Returns:
        JSON:
            {
            "status": "string",                 # "success" or "failed"
            "message": "string",                # Outcome of the schedule look up process
            "statusCode": Integer,              # The status code of the email
            "email_status": "string",           # status of the email
            "scheduled_time": "string",         # when the email is scheduled to be sent out
            "sent_at": "string"                 # when the email was sent out (if has been already)
            }
    """
    try:
        with get_db() as db:
            email = find_in_db(db, ScheduledEmail, schedule_id=schedule_id)
            
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

"""
@app.route("/unsubscribe")
def unsubscribe():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Error: Missing email parameter"}), 400

    with get_db() as db:
        if unsubscribe_email(db, email):
            return jsonify({"message": f"{email} unsubscribed successfully."}), 200
        else:
            return jsonify({"message": "You are already unsubscribed."}), 200
"""
            
# ------------------------
#   UI ROUTES
# ------------------------

adminCode = os.getenv("ADMIN_CODE")

@app.template_filter('friendly_datetime')
def friendly_datetime(value, format="%B %d, %Y at %I:%M %p"):
    """ Convert the date info from the database into a human readable format

    Args:
        value (str): The incoming dateTime string
        format (str): The format options for the returned dateTime string.

    Returns:
        str: The formatted dateTime string 
    """
    if not value:
        return "NULL"
    if isinstance(value, str):
        # Convert ISO string to datetime
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.strftime(format)

@app.route("/")
def index():
    """ Routes the user to the main UI page once opened
    
    Returns:
        rendering of templates/index.html
    """
    return render_template("index.html")

@app.route("/renderDebugMode", methods=["POST"])
def renderDebugMode():
    """ Routes the user to the admin pannel if the admin code
        From the "/" route matches the ADMIN_CODE env variable
    
    Returns:
        if the admin code is correct:
           redirect to the /admin route
        if the admin code is incoreect:
            rendering of templates/index.html 
    """
    client_ip = request.remote_addr;
    print(client_ip)
    if(request.form.get("AdminCode") == adminCode):
        return redirect(url_for("adminPannel", access_code = adminCode));
    return render_template("index.html")

@app.route("/admin/<access_code>")
def adminPannel(access_code):
    """ Routes the user to the admin pannel via 
        /admin/<access_code>?view=<view_name>

    Args:
        access_code (string): The access code for your program
        view_name (string): the name of the view you want to enter
                            in the admin pannel
            Options: ["emails", "timed_emails", "test_email"]
    
    Returns:
        if all arguments are correct / provided:
            rendering of the appropiate view from templates/admin-<view_name>View.html
        if access_code isn't valid:
            redirect to "/"
    """
    if access_code != adminCode:
        return redirect(url_for("index"))
    
    view = request.args.get("view")
    if view is None:
        # Redirect to same route with view="emails"
        return redirect(url_for("adminPannel", access_code=access_code, view="emails"))
    with get_db() as db:
        if view == "emails":
            data = db.query(EmailLog).all()  # All email logs
            return render_template("admin-emailsView.html", email_data=data, access_code=access_code)

        elif view == "timed_emails":
            data = db.query(ScheduledEmail).all()  # All scheduled emails
            return render_template("admin-timedEmailsView.html", email_data=data, access_code=access_code)

        elif view == "test_email":
            return render_template("admin-testEmailView.html", access_code=access_code)

@app.route("/send-test-email", methods=["POST"])
def sendTestEmail():
    """ HTTP Request that takes in an HTML form and creates a 
        test email based on the info in it
    
    Args:
        form.recipiant (Input[type="text"]): the email of the recipiant for the test email
        form.subject_line ((Input[type="text"])): subject line of email
        form.body (HTML): body of the email as HTML (use rich text editor)
        form.is_timed (Input[type="chechbox"]): Weather the email should be timed
        form.time_to_send (Input[type="time"]): The time to send (must be USC timezone)
        form.date_to_send (Input[type="date]): The date to send

    Returns: 
        JSON: The response from the "/send-email" or "/send-timed-email" 
        requests depending on if form.is_timed is provided.
    """
    print(request.method)
    print(request.form)
    recipient = request.form.get("recipiant")
    is_timed = "is_timed" in request.form
    if not is_timed:
        package = {
            "recipients": [recipient],
            "subject_line": request.form.get("subject"),
            "body": request.form.get("body"),
            "is_html": True
        }
        response = requests.post("http://127.0.0.1:5002/send-email", json=package)    
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return response.text, response.status_code
    else:
        package = {
            "recipients": [recipient],
            "subject_line": request.form.get("subject"),
            "body": request.form.get("body"),
            "is_html": True,
            "time_to_send": request.form.get("schedule_for_time"),
            "date_to_send": request.form.get("schedule_for_date")
        }
        
        response = requests.post("http://127.0.0.1:5002/send-timed-email", json=package)    
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return response.text, response.status_code

if __name__ == "__main__":
    # Init DB and start background scheduler only when running the app directly
    init_db()
    start_scheduler()
    port = int(os.getenv("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
