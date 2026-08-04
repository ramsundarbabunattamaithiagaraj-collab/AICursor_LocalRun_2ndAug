"""Pure-Python vector store fallback (no compiled native dependencies).

ChromaDB's default local index (chroma-hnswlib) requires a C++ toolchain to
build on Windows for Python versions without prebuilt wheels. To keep the
platform installable and runnable out of the box, this module provides a
minimal drop-in replacement exposing the same subset of the ChromaDB
collection API (`add`, `query`) used by RagService, backed by NumPy cosine
similarity and JSON persistence. If the real `chromadb` package (or its
optional `requirements-optional.txt` extras) is available, RagService
prefers it automatically.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SimpleVectorStore:
    """JSON-persisted, NumPy-backed cosine-similarity vector index."""

    def __init__(self, persist_path: Path):
        self.persist_path = persist_path
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._ids: list[str] = []
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._embeddings: list[list[float]] = []
        self._load()

    def _load(self) -> None:
        if not self.persist_path.exists():
            return
        try:
            data = json.loads(self.persist_path.read_text(encoding="utf-8"))
            self._ids = data.get("ids", [])
            self._documents = data.get("documents", [])
            self._metadatas = data.get("metadatas", [])
            self._embeddings = data.get("embeddings", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load vector store from %s: %s", self.persist_path, exc)

    def _save(self) -> None:
        payload = {
            "ids": self._ids,
            "documents": self._documents,
            "metadatas": self._metadatas,
            "embeddings": self._embeddings,
        }
        self.persist_path.write_text(json.dumps(payload), encoding="utf-8")

    def add(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        self._ids.extend(ids)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        self._embeddings.extend(embeddings)
        self._save()

    def query(self, query_embeddings: list[list[float]], n_results: int) -> dict:
        if not self._embeddings:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_vec = np.array(query_embeddings[0])
        matrix = np.array(self._embeddings)

        query_norm = np.linalg.norm(query_vec) or 1.0
        matrix_norms = np.linalg.norm(matrix, axis=1)
        matrix_norms[matrix_norms == 0] = 1.0

        similarities = (matrix @ query_vec) / (matrix_norms * query_norm)
        distances = 1 - similarities

        top_k = min(n_results, len(distances))
        top_indices = np.argsort(distances)[:top_k]

        return {
            "documents": [[self._documents[i] for i in top_indices]],
            "metadatas": [[self._metadatas[i] for i in top_indices]],
            "distances": [[float(distances[i]) for i in top_indices]],
        }

    def count(self) -> int:
        return len(self._ids)
