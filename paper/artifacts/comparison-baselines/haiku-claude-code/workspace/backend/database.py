from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# This will be overridden in tests
_current_session_local = SessionLocal


def set_session_local(session_local):
    """Override the session factory (used in tests)."""
    global _current_session_local
    _current_session_local = session_local


def get_db():
    db = _current_session_local()
    try:
        yield db
    finally:
        db.close()
