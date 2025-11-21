"""Database session management."""

from contextlib import contextmanager
from sqlalchemy.orm import Session
from .models import SessionLocal


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    """Get a database session (for dependency injection)."""
    return SessionLocal()
