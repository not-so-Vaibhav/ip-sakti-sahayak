"""Dual-Provider LLM Client module with automatic rate-limit failover."""

from backend.app.llm.client import LLMClient, llm_client

__all__ = ["LLMClient", "llm_client"]
