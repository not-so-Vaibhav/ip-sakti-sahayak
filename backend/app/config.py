"""Configuration settings for IP-SAKTI Sahayak."""

import os
from pathlib import Path
from typing import List, Optional, Union
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
    # Production / Demo default: sentence-transformers/all-MiniLM-L6-v2 (fast, lightweight, fits Render free tier)
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_use_mock: bool = True

    # Dual-Provider LLM Configuration (Gemini 2.5 Flash Primary + Groq Fallback + Optional Local Ollama)
    llm_provider_priority: Union[List[str], str] = ["gemini", "groq"]

    # Primary Provider: Google Gemini (Free tier via Google AI Studio)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # Fallback Provider: Groq (Free tier via Groq Console)
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.8-27b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Optional Local LLM Generation via Ollama
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_api_key: str = "ollama"

    @property
    def provider_priority_list(self) -> List[str]:
        """Returns provider priority as a clean list of strings."""
        if isinstance(self.llm_provider_priority, str):
            return [p.strip().lower() for p in self.llm_provider_priority.split(",") if p.strip()]
        return [p.strip().lower() for p in self.llm_provider_priority if p.strip()]

    # Tunable Retrieval & Confidence Parameters
    confidence_threshold: float = 0.50
    hybrid_dense_weight: float = 0.60
    hybrid_sparse_weight: float = 0.40
    top_k_retrieval: int = 5
    generation_timeout_seconds: float = 35.0
    generation_temperature: float = 0.1
    generation_presence_penalty: float = 0.0
    generation_frequency_penalty: float = 0.0

    # Investigation Mode — External Search APIs
    serpapi_key: Optional[str] = None
    semantic_scholar_timeout: float = 10.0
    investigation_llm_timeout: float = 45.0
    max_evidence_per_source: int = 10

    # File Paths
    tree_config_path: str = "config/decision_tree.json"
    categories_config_path: str = "config/formulation_categories_seed.json"
    seed_patents_path: str = "config/seed_patents.json"
    seed_formulations_path: str = "config/seed_formulations.json"
    ingredient_synonyms_path: str = "config/ingredient_synonyms.json"

    # Environment
    app_env: str = "development"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent / ".env"),
            ".env",
        ),
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
