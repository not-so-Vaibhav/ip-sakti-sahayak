"""Health and Corpus status endpoints."""

from fastapi import APIRouter
from backend.app.config import settings
from backend.app.db.qdrant_client import qdrant_manager
from backend.app.db.supabase_client import supabase_manager
from backend.app.ingestion.embedder import get_default_embedder
from backend.app.llm.client import llm_client

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health status")
async def health_check():
    """Returns status of database connections, embedder, dual-provider LLM, and configuration."""
    qdrant_ok = qdrant_manager.is_healthy()
    embedder = get_default_embedder()

    return {
        "status": "ok",
        "app_env": settings.app_env,
        "llm": llm_client.get_telemetry_status(),
        "qdrant": {
            "status": "connected" if qdrant_ok else "disconnected",
            "host": f"{settings.qdrant_host}:{settings.qdrant_port}",
            "collection": settings.qdrant_collection_name,
        },
        "supabase": {
            "status": "connected" if supabase_manager.is_connected else "detached",
        },
        "embedding_model": {
            "name": embedder.model_name,
            "dimension": embedder.dimension,
        },
        "retrieval_tuning": {
            "confidence_threshold": settings.confidence_threshold,
            "hybrid_dense_weight": settings.hybrid_dense_weight,
            "hybrid_sparse_weight": settings.hybrid_sparse_weight,
            "top_k": settings.top_k_retrieval,
        },
    }
