import threading
import time
from datetime import datetime, timezone, timedelta

from database import get_db, save_email_log
from models import ScheduledEmail, EmailLog
from email_sender import send_email

CHECK_INTERVAL_SECONDS = 60  # Check each 60 seconds
PURGE_DAYS = 7               # Purge emails sent after this many days

def _fetch_due_scheduled_emails(db):
    """ Gets the scheduled emails where the scheduled_time is now or already happened
        and the email is not processed yet
    
    Args:
        db (database session): The open session of the database

    Returns:
        All the emails that haven't been sent out yet and should be.
    """
    now = datetime.now(timezone.utc)
    return db.query(ScheduledEmail).filter(
        ScheduledEmail.status == "scheduled",
        ScheduledEmail.scheduled_time <= now
    ).all()


def _process_single_email(db, scheduled: ScheduledEmail):
    """ Send a scheduled email and save the information into
        the email log of the database

    Args:
        db (database instance): The open session of the database
        scheduled (ScheduledEmail): The column of the email to send from email.db
    """
    recipients = [r.strip() for r in scheduled.recipients.split(",") if r.strip()]

    if not recipients:
        print(f"[scheduler] scheduled email {scheduled.schedule_id} has no valid recipients, skipping")
        scheduled.status = "failed"
        return

    # Attempt to send
    success, status_code, _ = send_email(
        recipients=recipients,
        subject=scheduled.subject_line,
        body=scheduled.body,
        is_html=scheduled.is_html
    )

    # Update scheduled email status
    now = datetime.now(timezone.utc)
    scheduled.status = "sent" if success else "failed"
    scheduled.sent_at = now if success else None
    scheduled.status_code = 200 if success else status_code

    # Log the email
    log_success = save_email_log(
        db,
        recipients=recipients,
        subject_line=scheduled.subject_line,
        body=scheduled.body,
        is_html=scheduled.is_html,
        success=success,
        status_code=status_code
    )
    if not log_success:
        print(f"[scheduler] Failed to log scheduled email {scheduled.schedule_id}")

def purge_logs(db):
    purge_date = datetime.now(timezone.utc) - timedelta(days=PURGE_DAYS)

    #Delete all logs after purge date
    db.query(EmailLog).filter(
        EmailLog.sent_at <= purge_date
    ).delete()

    db.query(ScheduledEmail).filter(
        ScheduledEmail.sent_at.isnot(None),
        ScheduledEmail.sent_at <= purge_date
    ).delete()

    db.commit()


def check_scheduled_emails_loop():
    """ This function is the main loop for the scheduler. It looks
        through all the scheduled emails to find ones that need to be sent
        ever minute, and attempts to send them.
    """
    while True:
        try:
            with get_db() as db:
                try:
                    due_list = _fetch_due_scheduled_emails(db)
                    print(f"[scheduler] now={datetime.now(timezone.utc).isoformat()} due={len(due_list)}")

                    for scheduled in due_list:
                        print(f"[scheduler] processing id={scheduled.schedule_id} at {scheduled.scheduled_time}")
                        _process_single_email(db, scheduled)

                    db.commit()  # commit all processed emails at once

                except Exception as inner:
                    db.rollback()
                    print(f"[scheduler] processing error: {inner}")
                
                purge_logs(db)

        except Exception as outer:
            print(f"[scheduler] unexpected error: {outer}")

        time.sleep(CHECK_INTERVAL_SECONDS)


def start_scheduler():
    """Start a background thread that stops when the app stops."""
    t = threading.Thread(target=check_scheduled_emails_loop, daemon=True)
    t.start()
    print("Email scheduler started")
