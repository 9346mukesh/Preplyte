"""Embedding model wrapper (BRD section 15, NFR Maintainability).

The model is configurable via the EMBEDDING_MODEL env var so it can be
swapped without touching retrieval or analysis code.
"""

from __future__ import annotations

from typing import List, Optional

from ..config import get_settings


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode texts into normalized embedding vectors (FR-03)."""
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]
