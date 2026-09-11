"""Configuration settings for IP-SAKTI Sahayak."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Qdrant Vector Database
    # Assumes `docker compose up -d` has been executed from the workspace root
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "ip_sakti_chunks"

    # Supabase (Postgres & Relational Metadata)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    database_url: Optional[str] = None

    # Embeddings
    # Local dev default: intfloat/multilingual-e5-base (768-dim)
    # Demo/Prod: intfloat/multilingual-e5-large (1024-dim)
    embedding_model_name: str = "intfloat/multilingual-e5-base"

    # Local LLM Generation via Ollama
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_api_key: str = "ollama"

    # Tunable Retrieval & Confidence Parameters
    confidence_threshold: float = 0.50
    hybrid_dense_weight: float = 0.60
    hybrid_sparse_weight: float = 0.40
    top_k_retrieval: int = 5
    generation_timeout_seconds: float = 35.0
    generation_temperature: float = 0.1
    generation_presence_penalty: float = 0.0
    generation_frequency_penalty: float = 0.0

    # File Paths
    tree_config_path: str = "config/decision_tree.json"
    categories_config_path: str = "config/formulation_categories_seed.json"

    # Environment
    app_env: str = "development"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolve_path(self, rel_or_abs_path: str) -> Path:
        """Resolve a path relative to the backend root if not absolute."""
        p = Path(rel_or_abs_path)
        if p.is_absolute():
            return p
        # Find backend directory root
        backend_root = Path(__file__).resolve().parent.parent
        return (backend_root / p).resolve()


# Singleton settings instance
settings = Settings()
