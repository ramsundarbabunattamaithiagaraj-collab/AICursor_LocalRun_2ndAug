from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    artifact_type: str = Field(..., min_length=1, max_length=80)
    rating: int = Field(..., ge=1, le=5)
    comments: str | None = Field(default=None, max_length=2000)
    improvements: str | None = Field(default=None, max_length=2000)


class FeedbackRead(FeedbackCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
