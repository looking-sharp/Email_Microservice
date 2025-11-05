#region imports
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from models import Base, EmailLog, ScheduledEmail
from contextlib import contextmanager
#endregion

# ------------------------
#   ENV + ENGINE SETUP
# ------------------------

load_dotenv()  # Load .env when this module is imported

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///email.db")

# Use check_same_thread only for SQLite connections
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory (no autocommit, no autoflush)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

utcnow = lambda: datetime.now(timezone.utc)


# ------------------------
#   DB INIT + SESSION MGMT
# ------------------------

def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db() -> Session:
    """
    Return a new database session.
    Use `with get_db() as db:` to close automatically
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------
#   GENERIC HELPERS
# ------------------------

def find_in_db(session: Session, model, **filters):
    """
    Generic function to find a record in any table using keyword filters.
    Example: find_in_db(db, User, email="user@example.com")
    """
    return session.query(model).filter_by(**filters).first()

def add_to_db(session, instance, return_bool=False):
    """
    Add and commit a new record to the database.

    Returns:
        If return_bool=True: (bool): True on success, False on failure.
        Else: (instance) returns the instance.
    """
    try:
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return True if return_bool else instance
    except Exception as e:
        session.rollback()
        if return_bool:
            return False
        raise e


#-------------------------
#   EMAIL LOG LOGIC
#-------------------------

def save_email_log(session, recipients, subject_line, body, is_html, success, status_code) -> bool:
    try:
        log = EmailLog(
            recipients=",".join(recipients),
            subject_line=subject_line,
            body=body,
            is_html=is_html,
            status="sent" if success else "failed",
            status_code=status_code,
            sent_at=datetime.now(timezone.utc) if success else None,
        )
        return add_to_db(session, log, return_bool=True)
    except:
        return False


def save_scheduled_email(session, schedule_id, recipients, subject_line, body, is_html, scheduled_dt, status="scheduled", status_code=201) -> bool:
    """
    Create and store a new ScheduledEmail record.
    Automatically generates a unique schedule_id.
    """
    try:
        scheduled_email = ScheduledEmail(
            schedule_id=schedule_id,
            recipients=",".join(recipients),
            subject_line=subject_line,
            body=body,
            is_html=is_html,
            scheduled_time=scheduled_dt,
            status=status,
            status_code=status_code,
            created_at=datetime.now(timezone.utc),
        )
        return add_to_db(session, scheduled_email, return_bool=True)
    except:
        return False

# ------------------------
#   UNSUBSCRIBE LOGIC TBI
# ------------------------

'''
def is_unsubscribed(session: Session, email: str) -> bool:
    """
    Check if an email is listed in the DoNotSendLog table.
    Returns True if unsubscribed, False otherwise.
    """
    return find_in_db(session, DoNotSendLog, email=email) is not None

def unsubscribe_email(session: Session, email: str, reason: str = "User unsubscribed") -> bool:
    """
    Add an email to the DoNotSendLog table if not already present.
    Returns True if added, False if already unsubscribed.
    """
    if is_unsubscribed(session, email):
        return False  # Already unsubscribed

    entry = DoNotSendLog(email=email, reason=reason, unsubscribed_at=utcnow())
    add_to_db(session, entry)
    return True
'''