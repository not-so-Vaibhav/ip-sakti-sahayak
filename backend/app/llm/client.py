"""Dual-Provider Rate-Limit-Resilient LLM Client for IP-SAKTI Sahayak.

Supports Google Gemini (primary), Groq (fallback), and local Ollama (dev),
with automatic failover on HTTP 429 (Rate Limit), 5xx server errors, and timeouts.
Tracks telemetry and surfaces real-time provider health.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Manages multi-provider dispatch, rate-limit failover, and telemetry tracking."""

    def __init__(self):
        self.last_provider_used: Optional[str] = None
        self.last_successful_call: Optional[str] = None
        self.fallback_triggered_count: int = 0
        self.provider_success_counts: Dict[str, int] = {"gemini": 0, "groq": 0, "ollama": 0}
        self.provider_failure_counts: Dict[str, int] = {"gemini": 0, "groq": 0, "ollama": 0}
        self.provider_last_error: Dict[str, Optional[str]] = {"gemini": None, "groq": None, "ollama": None}

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Returns connection settings for a given provider."""
        p = provider_name.lower().strip()
        if p == "gemini":
            return {
                "name": "gemini",
                "base_url": settings.gemini_base_url.rstrip("/"),
                "model": settings.gemini_model,
                "api_key": settings.gemini_api_key or "",
                "is_configured": bool(settings.gemini_api_key),
            }
        elif p == "groq":
            return {
                "name": "groq",
                "base_url": settings.groq_base_url.rstrip("/"),
                "model": settings.groq_model,
                "api_key": settings.groq_api_key or "",
                "is_configured": bool(settings.groq_api_key),
            }
        elif p == "ollama":
            return {
                "name": "ollama",
                "base_url": settings.ollama_base_url.rstrip("/"),
                "model": settings.ollama_model,
                "api_key": settings.ollama_api_key or "ollama",
                "is_configured": True,
            }
        else:
            return {
                "name": p,
                "base_url": "",
                "model": "",
                "api_key": "",
                "is_configured": False,
            }

    def get_candidate_providers(self) -> List[Dict[str, Any]]:
        """
        Determines the ordered list of eligible providers to try.
        Strictly prioritizes providers from provider_priority_list that have valid configurations.
        """
        priority_names = settings.provider_priority_list
        candidates = []
        for name in priority_names:
            cfg = self.get_provider_config(name)
            if cfg["name"] in ("gemini", "groq"):
                if cfg["is_configured"]:
                    candidates.append(cfg)
            elif cfg["name"] == "ollama":
                candidates.append(cfg)

        return candidates

    def get_active_primary_provider(self) -> str:
        """Returns the name of the currently active primary provider."""
        candidates = self.get_candidate_providers()
        return candidates[0]["name"] if candidates else "none"

    def call_chat_completions(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 600,
        timeout_seconds: Optional[float] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        custom_llm: Optional[Callable[[List[Dict[str, str]]], str]] = None,
    ) -> str:
        """
        Executes chat completion with automatic provider fallback on 429 / 5xx / timeouts.
        Max 3 attempts total across candidates with rapid exponential backoff.
        """
        if custom_llm is not None:
            return custom_llm(messages)

        candidates = self.get_candidate_providers()
        if not candidates:
            # If completely unconfigured, provide a clear error message
            msg = (
                "No active LLM provider configured. Please set GEMINI_API_KEY (Google AI Studio) "
                "or GROQ_API_KEY (Groq Console) in your .env file."
            )
            logger.error(msg)
            raise RuntimeError(msg)

        timeout = timeout_seconds or float(getattr(settings, "generation_timeout_seconds", 35.0))
        max_total_attempts = 3
        attempt_count = 0
        last_exception: Optional[Exception] = None

        # Try providers in order; cycle or retry on failover
        provider_index = 0
        while attempt_count < max_total_attempts and provider_index < len(candidates):
            current_provider = candidates[provider_index]
            provider_name = current_provider["name"]
            endpoint = f"{current_provider['base_url']}/chat/completions"
            headers = {
                "Authorization": f"Bearer {current_provider['api_key']}",
                "Content-Type": "application/json",
            }
            payload: Dict[str, Any] = {
                "model": current_provider["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if presence_penalty and presence_penalty != 0.0 and provider_name != "gemini":
                payload["presence_penalty"] = presence_penalty
            if frequency_penalty and frequency_penalty != 0.0 and provider_name != "gemini":
                payload["frequency_penalty"] = frequency_penalty

            attempt_count += 1
            logger.info(
                f"[LLM Dispatch] Attempt {attempt_count}/{max_total_attempts}: "
                f"Calling '{provider_name}' ({current_provider['model']})..."
            )

            try:
                with httpx.Client(timeout=timeout) as client:
                    res = client.post(endpoint, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # Telemetry updates on success
                        self.last_provider_used = provider_name
                        self.last_successful_call = datetime.now(timezone.utc).isoformat()
                        self.provider_success_counts[provider_name] = (
                            self.provider_success_counts.get(provider_name, 0) + 1
                        )
                        self.provider_last_error[provider_name] = None

                        if provider_index > 0:
                            self.fallback_triggered_count += 1
                            logger.warning(
                                f"[LLM Failover] Successfully served by fallback provider '{provider_name}' "
                                f"after primary failure."
                            )
                        else:
                            logger.info(f"[LLM Dispatch] Successfully served by primary provider '{provider_name}'.")

                        return content

                    # Handle 429 Rate Limit or 5xx Server Error
                    error_text = res.text[:200]
                    res.raise_for_status()

            except Exception as e:
                last_exception = e
                err_msg = f"{type(e).__name__}: {str(e)[:200]}"
                self.provider_failure_counts[provider_name] = (
                    self.provider_failure_counts.get(provider_name, 0) + 1
                )
                self.provider_last_error[provider_name] = err_msg
                logger.warning(
                    f"[LLM Error] Provider '{provider_name}' failed on attempt {attempt_count}: {err_msg}"
                )

                # If there is a fallback provider available, advance to it
                if provider_index + 1 < len(candidates):
                    provider_index += 1
                    logger.info(
                        f"[LLM Failover] Switching to fallback provider: '{candidates[provider_index]['name']}'"
                    )
                
                # Brief backoff before next attempt
                if attempt_count < max_total_attempts:
                    backoff_sec = min(1.0, 0.5 * attempt_count)
                    time.sleep(backoff_sec)

        logger.error(f"[LLM Exhausted] All {attempt_count} attempts failed across providers.")
        if last_exception:
            raise last_exception
        raise RuntimeError("LLM completion failed across all candidate providers.")

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Returns status and metrics for /health endpoint."""
        gemini_cfg = self.get_provider_config("gemini")
        groq_cfg = self.get_provider_config("groq")
        ollama_cfg = self.get_provider_config("ollama")

        return {
            "provider_priority": settings.provider_priority_list,
            "active_primary_provider": self.get_active_primary_provider(),
            "last_provider_used": self.last_provider_used,
            "last_successful_call": self.last_successful_call,
            "fallback_triggered_count": self.fallback_triggered_count,
            "providers": {
                "gemini": {
                    "api_key_configured": gemini_cfg["is_configured"],
                    "model": gemini_cfg["model"],
                    "success_count": self.provider_success_counts.get("gemini", 0),
                    "failure_count": self.provider_failure_counts.get("gemini", 0),
                    "last_error": self.provider_last_error.get("gemini"),
                },
                "groq": {
                    "api_key_configured": groq_cfg["is_configured"],
                    "model": groq_cfg["model"],
                    "success_count": self.provider_success_counts.get("groq", 0),
                    "failure_count": self.provider_failure_counts.get("groq", 0),
                    "last_error": self.provider_last_error.get("groq"),
                },
                "ollama": {
                    "api_key_configured": True,
                    "model": ollama_cfg["model"],
                    "base_url": ollama_cfg["base_url"],
                    "success_count": self.provider_success_counts.get("ollama", 0),
                    "failure_count": self.provider_failure_counts.get("ollama", 0),
                    "last_error": self.provider_last_error.get("ollama"),
                },
            },
        }


# Global singleton LLM client
llm_client = LLMClient()
