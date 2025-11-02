from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

utcnow = lambda: datetime.now(timezone.utc)  

class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True, index=True)
    program_key = Column(String(255), nullable=False)
    recipients = Column(Text, nullable=False)
    subject_line = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    is_html = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    status_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)  
    sent_at = Column(DateTime(timezone=True), nullable=True)

class ScheduledEmail(Base):
    __tablename__ = "scheduled_emails"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String(64), unique=True, index=True, nullable=False)
    program_key = Column(String(255), nullable=False)
    recipients = Column(Text, nullable=False)
    subject_line = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    is_html = Column(Boolean, default=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="scheduled")
    created_at = Column(DateTime(timezone=True), default=utcnow)  
    sent_at = Column(DateTime(timezone=True), nullable=True)
