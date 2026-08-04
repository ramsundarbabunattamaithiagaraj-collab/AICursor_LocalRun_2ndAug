from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.rag_document import RagDocument
from app.repositories.base_repository import BaseRepository


class RagDocumentRepository(BaseRepository[RagDocument]):
    def __init__(self, db: Session):
        super().__init__(db, RagDocument)
