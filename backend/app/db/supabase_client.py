"""Supabase / Postgres Client Manager for IP-SAKTI Sahayak."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.config import settings

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
except ImportError:
    Client = None
    create_client = None


class SupabaseManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self._init_client()

    def _init_client(self) -> None:
        if not settings.supabase_url or not settings.supabase_key:
            logger.info("Supabase URL or Key not configured; running in detached/mock mode.")
            return

        if create_client is None:
            logger.warning("supabase-py library not installed.")
            return

        try:
            self.client = create_client(settings.supabase_url, settings.supabase_key)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    def record_classification_session(
        self,
        answers_json: Dict[str, Any],
        resulting_category: Optional[str],
        tree_version_tag: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[str]:
        """Insert or update classification session in Supabase."""
        if not self.is_connected:
            logger.debug("Supabase not connected. Session recorded locally in memory.")
            return session_id

        data = {
            "answers_json": answers_json,
            "resulting_category": resulting_category,
            "tree_version_tag": tree_version_tag,
        }
        if user_id:
            data["user_id"] = user_id
        if session_id:
            data["id"] = session_id

        try:
            res = self.client.table("classification_sessions").upsert(data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
        except Exception as e:
            logger.error(f"Error saving classification session to Supabase: {e}")
        return session_id

    def upsert_corpus_document(
        self,
        instrument_name: str,
        jurisdiction: str,
        regime_category: str,
        authority_level: str,
        source_url: str,
        effective_date: Optional[str] = None,
        last_amended_date: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Optional[str]:
        """Insert or update instrument document metadata."""
        if not self.is_connected:
            return document_id

        data = {
            "instrument_name": instrument_name,
            "jurisdiction": jurisdiction.lower(),
            "regime_category": regime_category.lower(),
            "authority_level": authority_level.lower(),
            "source_url": source_url,
            "effective_date": effective_date,
            "last_amended_date": last_amended_date,
        }
        if document_id:
            data["id"] = document_id

        try:
            res = self.client.table("corpus_documents").upsert(data, on_conflict="instrument_name,jurisdiction").execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
        except Exception as e:
            logger.error(f"Error upserting corpus document: {e}")
        return document_id

    def insert_corpus_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Batch insert clause-level chunks into Postgres."""
        if not self.is_connected:
            return True

        try:
            res = self.client.table("corpus_chunks").insert(chunks).execute()
            return bool(res.data)
        except Exception as e:
            logger.error(f"Error inserting corpus chunks to Supabase: {e}")
            return False

    def record_query_log(
        self,
        query_id: str,
        query_text: str,
        language: str,
        jurisdiction_selected: str,
        confidence_score: Optional[float] = None,
        abstained: bool = False,
        escalated: bool = False,
        answer_text: Optional[str] = None,
        user_id: Optional[str] = None,
        classification_session_id: Optional[str] = None,
    ) -> Optional[str]:
        """Record query log entry matching schema_mvp.sql query_logs table."""
        if not self.is_connected:
            return query_id

        data = {
            "id": query_id,
            "query_text": query_text,
            "language": language.lower(),
            "jurisdiction_selected": jurisdiction_selected.lower(),
            "confidence_score": confidence_score,
            "abstained": abstained,
            "escalated": escalated,
            "answer_text": answer_text,
        }
        if user_id:
            data["user_id"] = user_id
        if classification_session_id:
            data["classification_session_id"] = classification_session_id

        try:
            res = self.client.table("query_logs").insert(data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
        except Exception as e:
            logger.error(f"Error recording query log to Supabase: {e}")
        return query_id

    def record_query_citations(self, citations: List[Dict[str, Any]]) -> bool:
        """Record query citations matching schema_mvp.sql query_citations table."""
        if not self.is_connected or not citations:
            return True

        try:
            res = self.client.table("query_citations").insert(citations).execute()
            return bool(res.data)
        except Exception as e:
            logger.error(f"Error recording query citations to Supabase: {e}")
            return False


supabase_manager = SupabaseManager()
