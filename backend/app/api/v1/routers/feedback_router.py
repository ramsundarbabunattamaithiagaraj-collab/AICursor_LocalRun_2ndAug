from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> FeedbackRead:
    return FeedbackService(db).submit(payload)


@router.get("", response_model=list[FeedbackRead])
def list_feedback(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[FeedbackRead]:
    return FeedbackService(db).list(skip, limit)


@router.get("/average-rating")
def average_rating(artifact_type: str | None = None, db: Session = Depends(get_db)) -> dict:
    return {"artifact_type": artifact_type, "average_rating": FeedbackService(db).average_rating(artifact_type)}
