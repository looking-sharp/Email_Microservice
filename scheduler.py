import threading
import time
from datetime import datetime, timezone

from database import get_db
from models import ScheduledEmail, EmailLog
from email_sender import send_email

CHECK_INTERVAL_SECONDS = 60  # Check each 60 seconds


def _fetch_due_scheduled_emails(db):
    """Get scheduled emails (scheduled_time is now or in the past, and still not processed)"""
    now = datetime.now(timezone.utc)
    return db.query(ScheduledEmail).filter(
        ScheduledEmail.status == "scheduled",
        ScheduledEmail.scheduled_time <= now
    ).all()


def _process_single_email(db, scheduled: ScheduledEmail):
    """Send a scheduled email and update database."""
    recipients = [r.strip() for r in scheduled.recipients.split(",") if r.strip()]

    # Attempt to send
    success, status_code, message = send_email(
        recipients=recipients,
        subject=scheduled.subject_line,
        body=scheduled.body,
        is_html=scheduled.is_html
    )

    # Update scheduled email status
    if success:
        scheduled.status = "sent"
        scheduled.sent_at = datetime.now(timezone.utc)
    else:
        scheduled.status = "failed"

    # Write email log
    log = EmailLog(
        program_key=scheduled.program_key,
        recipients=scheduled.recipients,
        subject_line=scheduled.subject_line,
        body=scheduled.body,
        is_html=scheduled.is_html,
        status="sent" if success else "failed",
        status_code=status_code,
        sent_at=datetime.now(timezone.utc) if success else None
    )

    db.add(log)


def check_scheduled_emails_loop():
    while True:
        try:
            db = get_db()
            try:
                due_list = _fetch_due_scheduled_emails(db)
                print(f"[scheduler] now={datetime.now(timezone.utc).isoformat()} due={len(due_list)}")
                for scheduled in due_list:
                    print(f"[scheduler] processing id={scheduled.schedule_id} at {scheduled.scheduled_time}")
                    _process_single_email(db, scheduled)
                db.commit()
            except Exception as inner:
                db.rollback()
                print(f"[scheduler] processing error: {inner}")
            finally:
                db.close()
        except Exception as outer:
            print(f"[scheduler] unexpected error: {outer}")

        time.sleep(CHECK_INTERVAL_SECONDS)


def start_scheduler():
    """Start a background thread that stops when the app stops."""
    t = threading.Thread(target=check_scheduled_emails_loop, daemon=True)
    t.start()
    print("Email scheduler started")
