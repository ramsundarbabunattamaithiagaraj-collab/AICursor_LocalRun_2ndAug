"""Feedback capture to improve future generations (Section 14)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.rag_document import FeedbackRecord
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackService:
    def __init__(self, db: Session):
        self.repo = FeedbackRepository(db)

    def submit(self, payload: FeedbackCreate) -> FeedbackRecord:
        return self.repo.add(FeedbackRecord(**payload.model_dump()))

    def list(self, skip: int = 0, limit: int = 100) -> list[FeedbackRecord]:
        return self.repo.list(skip, limit)

    def average_rating(self, artifact_type: str | None = None) -> float:
        records = self.repo.list(limit=10_000)
        if artifact_type:
            records = [r for r in records if r.artifact_type == artifact_type]
        if not records:
            return 0.0
        return round(sum(r.rating for r in records) / len(records), 2)
