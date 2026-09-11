"""Qdrant Vector DB Client Manager for IP-SAKTI Sahayak.

Assumes `docker compose up -d` has been run from the project root.
Vector sizes are derived dynamically from the active embedding model.
"""

import logging
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient, models

from backend.app.config import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, api_key: Optional[str] = None):
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.api_key = api_key or settings.qdrant_api_key
        self.collection_name = settings.qdrant_collection_name
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                timeout=2,
            )
        return self._client

    def is_healthy(self) -> bool:
        """Check if Qdrant service is responding."""
        try:
            collections = self.client.get_collections()
            return collections is not None
        except Exception:
            return False

    def ensure_collection(self, vector_size: int, collection_name: Optional[str] = None) -> bool:
        """
        Ensure the collection exists with the exact vector dimension of the active embedder.
        Derives vector size dynamically from embedding configuration.
        """
        col_name = collection_name or self.collection_name
        try:
            collections_res = self.client.get_collections()
            existing_names = [c.name for c in collections_res.collections]

            if col_name not in existing_names:
                logger.info(f"Creating Qdrant collection '{col_name}' with dynamic vector_size={vector_size} (Cosine distance)...")
                self.client.create_collection(
                    collection_name=col_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                    sparse_vectors_config={
                        "bm25": models.SparseVectorParams(
                            index=models.SparseIndexParams(on_disk=False)
                        )
                    } if hasattr(models, "SparseVectorParams") else None,
                )
                self._create_payload_indexes(col_name)
            else:
                col_info = self.client.get_collection(col_name)
                vectors_cfg = col_info.config.params.vectors
                existing_dim = None
                if isinstance(vectors_cfg, models.VectorParams):
                    existing_dim = vectors_cfg.size
                elif isinstance(vectors_cfg, dict) and "" in vectors_cfg:
                    existing_dim = vectors_cfg[""].size

                if existing_dim and existing_dim != vector_size:
                    logger.warning(
                        f"Collection '{col_name}' exists with vector size {existing_dim}, "
                        f"but active embedder dimension is {vector_size}. Rebuilding collection..."
                    )
                    self.client.delete_collection(col_name)
                    return self.ensure_collection(vector_size, col_name)

                logger.info(f"Collection '{col_name}' already exists with matching dimension {vector_size}.")

            return True
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection '{col_name}': {e}")
            raise

    def _create_payload_indexes(self, collection_name: str) -> None:
        """Create keyword payload indexes required for fast pre-filtering per Backend Schema Section 5."""
        fields = [
            "jurisdiction",
            "regime_category",
            "formulation_category_relevance",
            "language",
            "authority_level",
            "instrument_name",
        ]
        for field in fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass

    def upsert_chunks(
        self,
        points: List[models.PointStruct],
        collection_name: Optional[str] = None,
    ) -> bool:
        """Upsert embedded points into Qdrant collection."""
        col_name = collection_name or self.collection_name
        try:
            self.client.upsert(
                collection_name=col_name,
                points=points,
                wait=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting points to Qdrant collection '{col_name}': {e}")
            raise


qdrant_manager = QdrantManager()
