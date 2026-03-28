"""Database engine and session factory."""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DB_PATH = _PROJECT_ROOT / "data" / "financial.db"

_engine = None
_SessionLocal = None


def init_db() -> None:
    """Create the database file, tables, and session factory. Call once at app startup."""
    global _engine, _SessionLocal
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(
        f"sqlite:///{_DB_PATH}",
        connect_args={"check_same_thread": False},
    )
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialised — call init_db() first.")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
