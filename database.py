import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base

load_dotenv()  # Load .env when this module is imported

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///email.db")

# Use check_same_thread only for SQLite connections
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory (no autocommit, no autoflush)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Return a new database session.
    The caller is responsible for calling `db.close()` after use.
    """
    return SessionLocal()

