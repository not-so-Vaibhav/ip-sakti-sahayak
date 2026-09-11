"""Citation-Constrained Generation Layer for IP-SAKTI Sahayak.

Enforces strict grounding on retrieved legal chunks, parses [cite:<chunk_id>] markers,
rejects hallucinated citations, and manages multi-turn retry loops with full context retention.
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import httpx

from backend.app.config import settings
from backend.app.generation.models import CitationItem, QueryResponse
from backend.app.retrieval.models import RetrievedChunk

logger = logging.getLogger(__name__)

# Regex to capture [cite: chunk-1], (cite: chunk-1), bare cite:chunk-1, [chunk-1], (chunk-1), and UUIDs
CITATION_PATTERN = re.compile(
    r"(?:\[|\()?\b(?:cite:\s*)?(chunk-[0-9]+|[a-f0-9\-]{36})\b(?:\]|\))?",
    re.IGNORECASE,
)


SYSTEM_PROMPT_TEMPLATE = """You are IP-SAKTI Sahayak, an authoritative legal and regulatory AI assistant specialized in Indian and International Intellectual Property, Biodiversity Access and Benefit Sharing (ABS), and regulatory frameworks for Ayurvedic formulations.

STRICT GROUNDING CONSTRAINTS:
1. You may ONLY make claims, assertions, or statements that are directly supported by the statutory clauses and legal text provided in the <legal_context> below.
2. DO NOT use external legal knowledge, general assumptions, or extrapolate beyond what is explicitly stated in the context.
3. If the provided context does not contain sufficient information to address any part of the query, explicitly state that the statutory provisions provided do not cover that aspect.
4. CITATION REQUIREMENT: Every single legal statement, rule, condition, threshold, or prohibition you write MUST be immediately followed by an inline citation marker referencing the exact short chunk ID: [cite:chunk-1], [cite:chunk-2], etc.
5. Do NOT invent, fabricate, or modify chunk IDs. Use ONLY the exact IDs given in the <chunk id="..."> tags.
6. Language: You must write your complete response in {language_name} ({language_code}). Even when responding in Hindi, keep citation tags in Latin characters like [cite:chunk-1], [cite:chunk-2].
7. Conciseness: Provide a structured legal answer (under 300 words). Do not repeat sentences or phrase loops."""


USER_PROMPT_TEMPLATE = """<legal_context>
{formatted_chunks}
</legal_context>

USER QUERY METADATA:
- Jurisdiction: {jurisdiction}
- Formulation Category: {formulation_category}
- Language: {language_name}

USER QUERY:
"{query_text}"

INSTRUCTIONS FOR ANSWER:
1. Provide a clear, concise, and structured legal analysis addressing the query.
2. Ground every claim directly in the legal context above using citation markers like [cite:chunk-1], [cite:chunk-2].
3. Detail the specific regulatory bar, exception, or statutory compliance requirement applicable to this formulation category.

CITATION FORMAT EXAMPLES:
- English: "Classical generic formulations cannot obtain product patents [cite:chunk-1]."
- Hindi: "शास्त्रीय नुस्खों को पेटेंट नहीं दिया जा सकता [cite:chunk-1]।"
Allowed Chunk IDs: {allowed_chunk_ids_str} (Cite ONLY from these IDs)."""


CORRECTION_PROMPT_TEMPLATE = """CORRECTION REQUIRED:
Your previous response failed validation because it cited invalid/unretrieved chunk IDs: {invalid_ids}.
You MUST ONLY cite short chunk IDs that exist inside the <legal_context> provided in the first message (Allowed IDs: {allowed_ids}).
Please re-generate your complete answer adhering strictly to the allowed chunk IDs."""


class CitationConstrainedGenerator:
    """Manages LLM interaction, grounding prompts, citation validation, and retries."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 2,
        llm_callable: Optional[Callable[[List[Dict[str, str]]], str]] = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.api_key = api_key or settings.ollama_api_key
        self.max_retries = max_retries
        self._custom_llm = llm_callable

    def _format_chunks_for_prompt(
        self,
        chunks: List[RetrievedChunk],
        uuid_to_short: Dict[str, str],
    ) -> str:
        """Formats retrieved chunks into clean statutory context blocks with request-scoped short IDs."""
        blocks = []
        for i, c in enumerate(chunks, start=1):
            short_id = uuid_to_short.get(c.chunk_id, f"chunk-{i}")
            sec = f"Section: {c.section_number}" if c.section_number else "Section: Unspecified"
            if c.parent_section_label:
                sec += f" ({c.parent_section_label})"

            block = (
                f'<chunk id="{short_id}">\n'
                f'Instrument: {c.instrument_name}\n'
                f'{sec}\n'
                f'Authority Level: {c.authority_level}\n'
                f'Text: {c.text_content}\n'
                f'</chunk>'
            )
            blocks.append(block)
        return "\n\n".join(blocks)

    def validate_citations(
        self,
        raw_text: str,
        allowed_chunk_ids: Set[str],
        retrieved_chunks: Optional[List[RetrievedChunk]] = None,
        uuid_to_short: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, List[str], List[str], str]:
        """
        Validates extracted citation markers against allowed retrieved chunk IDs (case-insensitive).
        Also matches statutory section mentions (e.g., Rule 122E, Section 3(d), धारा 3(p)) against retrieved chunks.
        Returns: (is_valid, valid_cited_ids_in_order, invalid_cited_ids, augmented_text)
        """
        if not raw_text:
            return False, [], ["no_text_generated"], raw_text

        matches = CITATION_PATTERN.findall(raw_text)
        valid_ids: List[str] = []
        invalid_ids: List[str] = []
        augmented_text = raw_text

        # Case-insensitive mapping for allowed IDs
        allowed_map = {cid.lower(): cid for cid in allowed_chunk_ids}

        for m in matches:
            cleaned = m.strip().lower()
            if cleaned in allowed_map:
                actual_id = allowed_map[cleaned]
                if actual_id not in valid_ids:
                    valid_ids.append(actual_id)
            else:
                invalid_ids.append(m)

        # Fallback grounding resolver: if no bracketed [cite:...] was parsed, scan for explicit statutory section mentions
        if not valid_ids and retrieved_chunks and uuid_to_short:
            for c in retrieved_chunks:
                if c.section_number:
                    sec_clean = c.section_number.strip()
                    # Match e.g. "122E", "3(a)", "3(d)", "3(p)", "Rule 122E", "Section 6", "धारा 3(p)"
                    pattern = re.compile(r"(?:section|sec|rule|धारा|नियम)?\s*" + re.escape(sec_clean), re.IGNORECASE)
                    if pattern.search(raw_text):
                        sid = uuid_to_short.get(c.chunk_id)
                        if sid and sid.lower() in allowed_map and sid not in valid_ids:
                            valid_ids.append(sid)
                            # Append citation marker to text
                            augmented_text += f" [cite:{sid}]"

        # Strict rule: at least 1 valid citation AND exactly 0 invalid citations
        is_valid = (len(valid_ids) >= 1) and (len(invalid_ids) == 0)
        return is_valid, valid_ids, invalid_ids, augmented_text

    def _call_llm_api(self, messages: List[Dict[str, str]]) -> str:
        """Executes LLM chat completion against Ollama / OpenAI-compatible endpoint."""
        if self._custom_llm is not None:
            return self._custom_llm(messages)

        endpoint = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": float(getattr(settings, "generation_temperature", 0.1)),
            "presence_penalty": float(getattr(settings, "generation_presence_penalty", 0.0)),
            "frequency_penalty": float(getattr(settings, "generation_frequency_penalty", 0.0)),
            "max_tokens": 600,
        }

        timeout_sec = float(getattr(settings, "generation_timeout_seconds", 35.0))
        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling LLM at {endpoint}: {e}")
            raise

    def generate_answer(
        self,
        query_text: str,
        jurisdiction: str,
        formulation_category: str,
        retrieved_chunks: List[RetrievedChunk],
        language: str = "en",
        confidence_score: float = 0.8,
    ) -> Tuple[Optional[str], List[CitationItem], bool, Optional[str], int]:
        """
        Generates grounded response with multi-turn citation validation.
        Request-scoped short IDs (chunk-1, chunk-2, ...) are mapped to real UUIDs.
        Returns: (answer_markdown, citations_list, abstained, abstention_reason, attempts_count)
        """
        if not retrieved_chunks:
            return (
                None,
                [],
                True,
                "No legal context provided for generation.",
                0,
            )

        lang_code = language.lower()
        lang_name = "Hindi" if lang_code == "hi" else "English"

        # Requirement 1: Fresh Request-Scoped Short-ID Mapping
        # Lives strictly within this function call / stack frame
        short_to_uuid: Dict[str, str] = {}
        uuid_to_short: Dict[str, str] = {}
        allowed_ids_for_validation: Set[str] = set()

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            short_id = f"chunk-{idx}"
            short_to_uuid[short_id.lower()] = chunk.chunk_id
            uuid_to_short[chunk.chunk_id] = short_id
            allowed_ids_for_validation.add(short_id.lower())
            # Also allow direct UUID if model happens to output it
            short_to_uuid[chunk.chunk_id.lower()] = chunk.chunk_id
            allowed_ids_for_validation.add(chunk.chunk_id.lower())

        chunk_lookup = {c.chunk_id: c for c in retrieved_chunks}
        formatted_context = self._format_chunks_for_prompt(retrieved_chunks, uuid_to_short)

        allowed_ids_str = ", ".join(f"chunk-{i}" for i in range(1, len(retrieved_chunks) + 1))

        system_msg = SYSTEM_PROMPT_TEMPLATE.format(
            language_name=lang_name,
            language_code=lang_code,
        )
        user_msg = USER_PROMPT_TEMPLATE.format(
            formatted_chunks=formatted_context,
            jurisdiction=jurisdiction.capitalize(),
            formulation_category=formulation_category,
            language_name=lang_name,
            query_text=query_text,
            allowed_chunk_ids_str=allowed_ids_str,
        )

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        attempt = 0
        last_raw_response: Optional[str] = None
        last_invalid_ids: List[str] = []

        while attempt <= self.max_retries:
            attempt += 1
            logger.info(f"Generating citation-constrained response (Attempt {attempt}/{self.max_retries + 1})...")

            try:
                raw_response = self._call_llm_api(messages)
                last_raw_response = raw_response
                logger.info(f"Raw LLM response (Attempt {attempt}):\n{raw_response}")
            except httpx.TimeoutException as e:
                timeout_val = float(getattr(settings, "generation_timeout_seconds", 35.0))
                logger.warning(f"LLM call timed out after {timeout_val}s on attempt {attempt}: {e}")
                return (
                    None,
                    [],
                    True,
                    f"Generation request timed out after {timeout_val:.0f}s. System gracefully abstained.",
                    attempt,
                )
            except Exception as e:
                logger.warning(f"LLM call failed on attempt {attempt}: {e}")
                if attempt > self.max_retries:
                    return (
                        None,
                        [],
                        True,
                        f"Generation service unavailable ({str(e)}).",
                        attempt,
                    )
                continue

            # Validate citations against request-scoped allowed IDs
            is_valid, valid_ids, invalid_ids, augmented_response = self.validate_citations(
                raw_response,
                allowed_ids_for_validation,
                retrieved_chunks=retrieved_chunks,
                uuid_to_short=uuid_to_short,
            )

            if is_valid:
                logger.info(f"Citation validation passed on attempt {attempt}. Cited short IDs: {valid_ids}")

                # Requirement 2 & 3: Resolve short IDs back to real UUIDs
                citations_list: List[CitationItem] = []
                for rank, sid in enumerate(valid_ids, start=1):
                    real_uuid = short_to_uuid[sid.lower()]
                    chunk_obj = chunk_lookup[real_uuid]
                    citations_list.append(
                        CitationItem(
                            chunk_id=real_uuid,  # ALWAYS the real database UUID
                            instrument_name=chunk_obj.instrument_name,
                            section_number=chunk_obj.section_number,
                            parent_section_label=chunk_obj.parent_section_label,
                            authority_level=chunk_obj.authority_level,
                            source_url=chunk_obj.source_url,
                            text_snippet=chunk_obj.text_content[:200] + ("..." if len(chunk_obj.text_content) > 200 else ""),
                            rank_position=rank,
                            retrieval_score=chunk_obj.combined_score,
                        )
                    )

                # Format raw response into displayable markdown with numbered footnotes [^1], [^2]
                formatted_answer = augmented_response
                for idx, sid in enumerate(valid_ids, start=1):
                    pattern = re.compile(rf"(?:\[|\()?\b(?:cite:\s*)?{re.escape(sid)}\b(?:\]|\))?", re.IGNORECASE)
                    formatted_answer = pattern.sub(f"[^{idx}]", formatted_answer)

                return formatted_answer, citations_list, False, None, attempt

            # Validation failed on this attempt
            last_invalid_ids = invalid_ids
            logger.warning(
                f"Citation validation failed on attempt {attempt}. "
                f"Invalid/unretrieved cited IDs: {invalid_ids}. Valid cited: {valid_ids}"
            )

            # If retries remaining, retain context in multi-turn format and send correction prompt with short IDs
            if attempt <= self.max_retries:
                messages.append({"role": "assistant", "content": raw_response})
                correction_msg = CORRECTION_PROMPT_TEMPLATE.format(
                    invalid_ids=", ".join(invalid_ids) if invalid_ids else "none",
                    allowed_ids=allowed_ids_str,
                )
                messages.append({"role": "user", "content": correction_msg})

        # Terminal Fallback: Retries exhausted without valid citation grounding -> Force Abstention
        logger.warning(
            f"All {attempt} generation attempts failed citation validation. Forcing terminal abstention."
        )
        return (
            None,
            [],
            True,
            "System abstained: Unable to verify strict citation grounding against legal sources after multiple validation attempts.",
            attempt,
        )


def get_default_generator(
    llm_callable: Optional[Callable[[List[Dict[str, str]]], str]] = None
) -> CitationConstrainedGenerator:
    return CitationConstrainedGenerator(llm_callable=llm_callable)
