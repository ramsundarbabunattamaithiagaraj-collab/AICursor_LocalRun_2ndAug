from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.rag_document import FeedbackRecord
from app.repositories.base_repository import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackRecord]):
    def __init__(self, db: Session):
        super().__init__(db, FeedbackRecord)
