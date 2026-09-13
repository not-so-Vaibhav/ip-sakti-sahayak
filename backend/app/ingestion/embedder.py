"""Multilingual Embedder interface for IP-SAKTI Sahayak.

Supports self-hosted sentence-transformers models (e.g., intfloat/multilingual-e5-base,
intfloat/multilingual-e5-large). Exposes dynamic vector dimension.
"""

import logging
from typing import List, Optional, Union
import numpy as np

from backend.app.config import settings

logger = logging.getLogger(__name__)


class MultilingualEmbedder:
    """Embedder using local sentence-transformers models or deterministic fallback."""

    def __init__(self, model_name: Optional[str] = None, use_mock: Optional[bool] = None):
        self.model_name = model_name or settings.embedding_model_name
        self.use_mock = use_mock if use_mock is not None else (settings.embedding_use_mock or self.model_name.lower() == "mock")
        self._model = None
        self._dimension: Optional[int] = self._infer_dimension(self.model_name)

    @staticmethod
    def _infer_dimension(name: str) -> int:
        name_lower = name.lower()
        if "large" in name_lower:
            return 1024
        elif "base" in name_lower:
            return 768
        elif "small" in name_lower or "mini" in name_lower:
            return 384
        return 768

    @property
    def dimension(self) -> int:
        """Dynamically return the embedding dimension."""
        if not self.use_mock and self._model is not None and hasattr(self._model, "get_sentence_embedding_dimension"):
            return self._model.get_sentence_embedding_dimension()
        return self._dimension or self._infer_dimension(self.model_name)

    @property
    def model(self):
        if self.use_mock:
            return None

        if self._model is None:
            logger.info(f"Loading local embedding model: '{self.model_name}'...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded. Dimension: {self._dimension}")
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer('{self.model_name}'): {e}. "
                    "Using deterministic mock embeddings for offline testing."
                )
        return self._model

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        """
        Embed document passages. E5 models expect 'passage: ' prefix.
        """
        if not texts:
            return []

        prefixed = [
            f"passage: {t.strip()}" if "e5" in self.model_name.lower() and not t.startswith("passage:") else t
            for t in texts
        ]

        if not self.use_mock and self.model is not None:
            embeddings = self.model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist() if isinstance(embeddings, np.ndarray) else [e.tolist() for e in embeddings]

        # Deterministic pseudo-embedding fallback for unit tests if model weights are unavailable or in mock mode
        dim = self.dimension
        results = []
        for text in texts:
            seed = sum(ord(c) for c in text[:64])
            rng = np.random.RandomState(seed)
            vec = rng.randn(dim)
            vec = vec / np.linalg.norm(vec)
            results.append(vec.tolist())
        return results

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single search query. E5 models expect 'query: ' prefix.
        """
        formatted = f"query: {query.strip()}" if "e5" in self.model_name.lower() and not query.startswith("query:") else query

        if not self.use_mock and self.model is not None:
            embedding = self.model.encode(formatted, normalize_embeddings=True, show_progress_bar=False)
            return embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)

        dim = self.dimension
        seed = sum(ord(c) for c in query[:64])
        rng = np.random.RandomState(seed)
        vec = rng.randn(dim)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()


def get_default_embedder(use_mock: Optional[bool] = None) -> MultilingualEmbedder:
    return MultilingualEmbedder(use_mock=use_mock)
