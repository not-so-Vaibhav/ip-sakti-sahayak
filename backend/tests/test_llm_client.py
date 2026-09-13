"""Unit tests for Dual-Provider LLM Client with automatic rate-limit failover."""

import pytest
import httpx
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.llm.client import LLMClient
from backend.app.main import app


def test_candidate_provider_resolution():
    """Verify priority-based candidate provider resolution."""
    client = LLMClient()
    
    # When both Gemini and Groq have keys configured
    with patch.object(settings, "gemini_api_key", "test_gemini_key"), \
         patch.object(settings, "groq_api_key", "test_groq_key"), \
         patch.object(settings, "llm_provider_priority", ["gemini", "groq"]):
        candidates = client.get_candidate_providers()
        names = [c["name"] for c in candidates]
        assert names == ["gemini", "groq"]
        assert client.get_active_primary_provider() == "gemini"

    # When priority is inverted
    with patch.object(settings, "gemini_api_key", "test_gemini_key"), \
         patch.object(settings, "groq_api_key", "test_groq_key"), \
         patch.object(settings, "llm_provider_priority", ["groq", "gemini"]):
        candidates = client.get_candidate_providers()
        names = [c["name"] for c in candidates]
        assert names == ["groq", "gemini"]
        assert client.get_active_primary_provider() == "groq"


def test_successful_call_on_primary():
    """Verify standard successful call on primary provider without fallback."""
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Grounded answer from Gemini"}}]
    }

    with patch.object(settings, "gemini_api_key", "test_gemini_key"), \
         patch.object(settings, "groq_api_key", "test_groq_key"), \
         patch.object(settings, "llm_provider_priority", ["gemini", "groq"]), \
         patch("httpx.Client.post", return_value=mock_response) as mock_post:

        result = client.call_chat_completions(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result == "Grounded answer from Gemini"
        assert client.last_provider_used == "gemini"
        assert client.fallback_triggered_count == 0
        assert client.provider_success_counts["gemini"] == 1
        assert mock_post.call_count == 1


def test_automatic_fallback_on_429_rate_limit():
    """Verify that a 429 Rate Limit on Gemini triggers automatic failover to Groq."""
    client = LLMClient()

    gemini_429_response = MagicMock()
    gemini_429_response.status_code = 429
    gemini_429_response.text = "Rate limit exceeded (TPM/RPM)"
    gemini_429_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "429 Too Many Requests",
        request=MagicMock(),
        response=gemini_429_response,
    )

    groq_200_response = MagicMock()
    groq_200_response.status_code = 200
    groq_200_response.json.return_value = {
        "choices": [{"message": {"content": "Grounded answer from Groq fallback"}}]
    }

    def mock_post_side_effect(endpoint, json=None, headers=None):
        if "generativelanguage" in endpoint:
            return gemini_429_response
        elif "groq" in endpoint:
            return groq_200_response
        return gemini_429_response

    with patch.object(settings, "gemini_api_key", "test_gemini_key"), \
         patch.object(settings, "groq_api_key", "test_groq_key"), \
         patch.object(settings, "llm_provider_priority", ["gemini", "groq"]), \
         patch("time.sleep", return_value=None), \
         patch("httpx.Client.post", side_effect=mock_post_side_effect):

        result = client.call_chat_completions(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result == "Grounded answer from Groq fallback"
        assert client.last_provider_used == "groq"
        assert client.fallback_triggered_count == 1
        assert client.provider_failure_counts["gemini"] == 1
        assert client.provider_success_counts["groq"] == 1


def test_automatic_fallback_on_server_error_and_timeout():
    """Verify that a 500 error or ReadTimeout triggers failover to fallback provider."""
    client = LLMClient()

    groq_200_response = MagicMock()
    groq_200_response.status_code = 200
    groq_200_response.json.return_value = {
        "choices": [{"message": {"content": "Recovered by Groq"}}]
    }

    def mock_post_side_effect(endpoint, json=None, headers=None):
        if "generativelanguage" in endpoint:
            raise httpx.ReadTimeout("Gemini connection timed out")
        elif "groq" in endpoint:
            return groq_200_response
        raise RuntimeError("Unexpected endpoint")

    with patch.object(settings, "gemini_api_key", "test_gemini_key"), \
         patch.object(settings, "groq_api_key", "test_groq_key"), \
         patch.object(settings, "llm_provider_priority", ["gemini", "groq"]), \
         patch("time.sleep", return_value=None), \
         patch("httpx.Client.post", side_effect=mock_post_side_effect):

        result = client.call_chat_completions(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result == "Recovered by Groq"
        assert client.last_provider_used == "groq"
        assert client.fallback_triggered_count == 1
        assert client.provider_failure_counts["gemini"] == 1
        assert client.provider_success_counts["groq"] == 1


def test_health_endpoint_reports_dual_provider_telemetry():
    """Verify /health endpoint returns detailed dual-provider LLM status."""
    test_client = TestClient(app)
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "llm" in data
    llm_info = data["llm"]
    assert "provider_priority" in llm_info
    assert "active_primary_provider" in llm_info
    assert "providers" in llm_info
    assert "gemini" in llm_info["providers"]
    assert "groq" in llm_info["providers"]
    assert "ollama" in llm_info["providers"]
