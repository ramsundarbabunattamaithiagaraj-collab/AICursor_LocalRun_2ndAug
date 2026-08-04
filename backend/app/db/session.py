"""Database engine and session factory."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_backend_root, get_settings

settings = get_settings()

_db_url = settings.database.url
if _db_url.startswith("sqlite:///./"):
    relative_path = _db_url.replace("sqlite:///./", "")
    absolute_path = get_backend_root() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    _db_url = f"sqlite:///{absolute_path}"

connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, echo=settings.database.echo, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
