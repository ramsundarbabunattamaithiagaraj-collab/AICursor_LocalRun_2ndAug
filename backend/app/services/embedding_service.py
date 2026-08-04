"""Text embedding provider with graceful fallback.

Tries the configured transformer model (default: BAAI/bge-base-en-v1.5).
If sentence-transformers or the model weights are unavailable (no internet,
package missing, etc.) it falls back to a lightweight deterministic hashing
embedding so the RAG pipeline keeps working end-to-end without crashing the
whole application - this favors availability over embedding quality when
offline, and is logged clearly so it is never silent.
"""
from __future__ import annotations

import hashlib
import math

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_HASH_DIMENSIONS = 384


class EmbeddingService:
    _instance: "EmbeddingService | None" = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._mode = "hash"
        self._load_model()

    def _load_model(self) -> None:
        for model_name in (self.settings.rag.embedding_model, self.settings.rag.fallback_embedding_model):
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(model_name)
                self._mode = "sentence_transformers"
                logger.info("Loaded embedding model: %s", model_name)
                return
            except Exception as exc:  # noqa: BLE001 - any load failure triggers fallback
                logger.warning("Could not load embedding model '%s': %s", model_name, exc)

        logger.warning(
            "Falling back to lightweight hashing embeddings. "
            "Install 'sentence-transformers' and ensure internet access for higher quality retrieval."
        )
        self._mode = "hash"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._mode == "sentence_transformers" and self._model is not None:
            return self._model.encode(texts, normalize_embeddings=True).tolist()
        return [self._hash_embed(text) for text in texts]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    @staticmethod
    def _hash_embed(text: str, dims: int = _HASH_DIMENSIONS) -> list[float]:
        vector = [0.0] * dims
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            index = int(digest, 16) % dims
            vector[index] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    @property
    def mode(self) -> str:
        return self._mode


def get_embedding_service() -> EmbeddingService:
    if EmbeddingService._instance is None:
        EmbeddingService._instance = EmbeddingService()
    return EmbeddingService._instance
