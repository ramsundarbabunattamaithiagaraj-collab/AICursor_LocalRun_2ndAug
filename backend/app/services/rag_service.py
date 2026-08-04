"""Retrieval-Augmented Generation service (Section 6).

Ingests PDFs (text/table/image aware via PdfExtractionService), chunks and
embeds content, stores it in ChromaDB, and answers questions by retrieving
the most relevant chunks. Custom/local approved documents are prioritized
over any external knowledge (Priority Rule) by only ever retrieving from the
locally ingested collection.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from app.core.config import get_backend_root, get_settings
from app.core.logging_config import get_logger
from app.schemas.rag import RagQueryResponse, RagSourceChunk
from app.services.embedding_service import get_embedding_service
from app.services.pdf_extraction_service import ExtractedChunk, PdfExtractionService
from app.services.vector_store import SimpleVectorStore
from app.utils.exceptions import RagUnavailableError

logger = get_logger(__name__)

_COLLECTION_NAME = "retail_knowledge_base"


class RagService:
    _client = None
    _collection = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()
        self.pdf_service = PdfExtractionService()
        self._ensure_client()

    def _ensure_client(self) -> None:
        if RagService._collection is not None:
            return

        persist_dir = get_backend_root() / self.settings.rag.persist_directory
        persist_dir.mkdir(parents=True, exist_ok=True)

        try:
            import chromadb

            RagService._client = chromadb.PersistentClient(path=str(persist_dir))
            RagService._collection = RagService._client.get_or_create_collection(
                name=_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection ready at %s", persist_dir)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ChromaDB unavailable (%s). Falling back to the built-in lightweight "
                "vector store. Install 'chromadb' (see requirements-optional.txt) for "
                "a production-grade vector database.", exc,
            )

        try:
            RagService._collection = SimpleVectorStore(persist_dir / "simple_store.json")
            logger.info("Lightweight vector store ready at %s", persist_dir)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to initialize fallback vector store: %s", exc)
            RagService._client = None
            RagService._collection = None

    def _require_collection(self):
        if RagService._collection is None:
            raise RagUnavailableError(
                "Vector database is not available. Ensure 'chromadb' is installed correctly."
            )
        return RagService._collection

    def _chunk_text(self, text: str) -> list[str]:
        size = self.settings.rag.chunk_size
        overlap = self.settings.rag.chunk_overlap
        if len(text) <= size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start = end - overlap
            if start < 0:
                start = 0
        return chunks

    def ingest_pdf(self, file_path: str) -> tuple[int, list[str]]:
        collection = self._require_collection()
        image_dir = str(get_backend_root() / "data" / "extracted_images")
        extracted: list[ExtractedChunk] = self.pdf_service.extract(file_path, image_dir)

        documents: list[str] = []
        metadatas: list[dict] = []
        ids: list[str] = []

        for chunk in extracted:
            pieces = self._chunk_text(chunk.content) if chunk.content_type == "text" else [chunk.content]
            for piece in pieces:
                documents.append(piece)
                metadatas.append(
                    {
                        "source_file": chunk.source_file,
                        "page_number": chunk.page_number,
                        "content_type": chunk.content_type,
                    }
                )
                ids.append(str(uuid.uuid4()))

        if not documents:
            logger.warning("No extractable content found in %s", file_path)
            return 0, []

        embeddings = self.embedding_service.embed(documents)
        collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

        content_types = sorted({m["content_type"] for m in metadatas})
        logger.info("Ingested %s chunks from %s into RAG collection.", len(documents), file_path)
        return len(documents), content_types

    def query(self, question: str, top_k: int | None = None) -> RagQueryResponse:
        collection = self._require_collection()
        k = top_k or self.settings.rag.top_k

        query_embedding = self.embedding_service.embed_one(question)
        results = collection.query(query_embeddings=[query_embedding], n_results=k)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        sources: list[RagSourceChunk] = []
        for doc, meta, distance in zip(documents, metadatas, distances):
            score = max(0.0, 1 - distance)
            sources.append(
                RagSourceChunk(
                    document=meta.get("source_file", "unknown"),
                    page=meta.get("page_number"),
                    content_type=meta.get("content_type", "text"),
                    snippet=doc[:400],
                    score=round(score, 4),
                )
            )

        answer = self._synthesize_answer(question, sources)
        context_relevance = round(sum(s.score for s in sources) / len(sources), 4) if sources else 0.0
        confidence = round(min(0.95, context_relevance * 0.9 + (0.1 if sources else 0)), 4)

        return RagQueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            context_relevance=context_relevance,
        )

    @staticmethod
    def _synthesize_answer(question: str, sources: list[RagSourceChunk]) -> str:
        """Extractive answer synthesis (no external LLM call required).

        When an LLM provider is configured (OPENAI_API_KEY), the
        AgentOrchestrationService can be used instead for generative answers;
        this keeps the core RAG query path usable with zero external
        dependencies/cost.
        """
        if not sources:
            return (
                "No relevant information was found in the knowledge base for this question. "
                "Try ingesting relevant product catalogs, price lists, or policy documents first."
            )
        top = sources[0]
        combined = " ".join(s.snippet for s in sources[:3])
        return (
            f"Based on '{top.document}' (page {top.page}, {top.content_type} content) and "
            f"{len(sources) - 1} other related chunk(s): {combined[:600]}"
        )


_rag_service_singleton: RagService | None = None


def get_rag_service() -> RagService:
    global _rag_service_singleton
    if _rag_service_singleton is None:
        _rag_service_singleton = RagService()
    return _rag_service_singleton
