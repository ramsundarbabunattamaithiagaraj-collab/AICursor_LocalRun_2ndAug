from __future__ import annotations

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RagSourceChunk(BaseModel):
    document: str
    page: int | None = None
    content_type: str
    snippet: str
    score: float


class RagQueryResponse(BaseModel):
    answer: str
    sources: list[RagSourceChunk]
    confidence: float
    context_relevance: float


class RagIngestResponse(BaseModel):
    file_name: str
    chunk_count: int
    content_types: list[str]
    status: str
