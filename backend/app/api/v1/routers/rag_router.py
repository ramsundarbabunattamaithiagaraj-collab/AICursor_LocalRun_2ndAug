from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_backend_root
from app.db.session import get_db
from app.models.rag_document import RagDocument
from app.repositories.rag_document_repository import RagDocumentRepository
from app.schemas.rag import RagIngestResponse, RagQueryRequest, RagQueryResponse
from app.services.rag_service import get_rag_service
from app.utils.exceptions import RagUnavailableError

router = APIRouter(prefix="/api/v1/rag", tags=["RAG Knowledge Assistant"])

_UPLOAD_DIR = get_backend_root() / "data" / "uploaded_documents"


@router.post("/ingest", response_model=RagIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> RagIngestResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = _UPLOAD_DIR / file.filename
    contents = await file.read()
    destination.write_bytes(contents)

    doc_repo = RagDocumentRepository(db)
    record = RagDocument(
        file_name=file.filename, source_path=str(destination), status="processing"
    )
    doc_repo.add(record)

    try:
        chunk_count, content_types = get_rag_service().ingest_pdf(str(destination))
        record.chunk_count = chunk_count
        record.content_types = ",".join(content_types) if content_types else "none"
        record.status = "ready" if chunk_count else "empty"
        doc_repo.commit_refresh(record)
    except RagUnavailableError as exc:
        record.status = "failed"
        doc_repo.commit_refresh(record)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return RagIngestResponse(
        file_name=file.filename,
        chunk_count=record.chunk_count,
        content_types=record.content_types.split(","),
        status=record.status,
    )


@router.post("/query", response_model=RagQueryResponse)
def query_knowledge_base(payload: RagQueryRequest) -> RagQueryResponse:
    try:
        return get_rag_service().query(payload.question, payload.top_k)
    except RagUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)) -> list[dict]:
    records = RagDocumentRepository(db).list(limit=500)
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "content_types": r.content_types,
            "chunk_count": r.chunk_count,
            "status": r.status,
            "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in records
    ]
