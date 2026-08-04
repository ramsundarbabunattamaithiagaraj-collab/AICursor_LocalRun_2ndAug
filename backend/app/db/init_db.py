"""Create all database tables. Import all models here so metadata is complete."""
from __future__ import annotations

from app.core.logging_config import get_logger
from app.db.base import Base
from app.db.session import engine
from app.models import (  # noqa: F401
    category,
    customer,
    inventory,
    order,
    product,
    rag_document,
    user,
)

logger = get_logger(__name__)


def init_db() -> None:
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")
