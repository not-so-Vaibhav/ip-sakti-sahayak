"""Formulation Extraction Engine for IP-SAKTI Sahayak.

Parses free-text formulation descriptions into structured FormulationElement objects
using LLM-constrained JSON extraction with regex fallback.
"""

import json
import logging
import re
from typing import Dict, List, Optional

import httpx

from backend.app.config import settings
from backend.app.investigation.models import FormulationElement, StructuredFormulation

logger = logging.getLogger(__name__)

# Known Ayurvedic process keywords for regex fallback
KNOWN_PROCESSES = [
    "steam extraction", "steam distillation", "cold press", "cold pressed",
    "fermentation", "decoction", "kwath", "kashaya", "bhavana", "shodhana",
    "marana", "calcination", "trituration", "distillation", "infusion",
    "maceration", "percolation", "soxhlet extraction", "hydro-distillation",
    "supercritical co2", "spray drying", "lyophilization", "standardized extract",
]

KNOWN_DOSAGE_FORMS = [
    "tablet", "capsule", "churna", "powder", "syrup", "kwath", "asava",
    "arishta", "bhasma", "guggulu", "vati", "gutika", "taila", "oil",
    "ghrita", "ghee", "lepa", "paste", "ointment", "cream", "drops",
    "rasa", "pisti", "avaleha", "lehya",
]

EXTRACTION_SYSTEM_PROMPT = """You are a pharmaceutical formulation parser. Extract structured elements from Ayurvedic/botanical formulation descriptions.

OUTPUT FORMAT: Return ONLY valid JSON, no markdown, no explanation. The JSON must be an object with these keys:
{
  "ingredients": [{"name": "...", "value": null}],
  "ratios": [{"name": "ratio description", "value": "3:1"}],
  "processes": [{"name": "steam extraction", "value": null}],
  "dosage_forms": [{"name": "tablet", "value": null}],
  "intended_uses": [{"name": "inflammation", "value": null}]
}

RULES:
1. Extract ALL ingredients mentioned (herbs, minerals, metals, animal products).
2. Extract numeric ratios if mentioned.
3. Extract manufacturing/preparation processes.
4. Extract dosage forms (tablet, capsule, churna, etc.).
5. Extract intended therapeutic uses.
6. If information for a category is not present, return an empty array [].
7. Use the original language for ingredient names but add botanical names if obvious.
8. DO NOT invent or hallucinate ingredients not mentioned in the input."""

EXTRACTION_USER_PROMPT = """Parse this formulation description into structured elements:

"{formulation_text}"

Return ONLY the JSON object."""


class FormulationExtractor:
    """Extracts structured formulation data from free-text descriptions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.api_key = api_key or settings.ollama_api_key

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Calls the LLM endpoint (same pattern as generator.py)."""
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.05,
            "max_tokens": 800,
        }
        timeout_sec = getattr(settings, "investigation_llm_timeout", 45.0)
        with httpx.Client(timeout=timeout_sec) as client:
            res = client.post(endpoint, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    def _parse_llm_json(self, raw: str) -> Optional[Dict]:
        """Attempts to parse LLM output as JSON, stripping markdown fences if present."""
        cleaned = raw.strip()
        # Strip markdown code fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object within the text
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return None

    def _regex_fallback(self, text: str) -> Dict[str, List[Dict]]:
        """Regex-based heuristic extraction when LLM fails."""
        result: Dict[str, List[Dict]] = {
            "ingredients": [],
            "ratios": [],
            "processes": [],
            "dosage_forms": [],
            "intended_uses": [],
        }

        text_lower = text.lower()

        # Extract ratios (patterns like "3:1", "2:1:1", "1 part : 2 parts")
        ratio_matches = re.findall(r"\b(\d+(?:\.\d+)?(?:\s*:\s*\d+(?:\.\d+)?)+)\b", text)
        for r in ratio_matches:
            result["ratios"].append({"name": f"ratio {r}", "value": r.replace(" ", "")})

        # Extract known processes
        for proc in KNOWN_PROCESSES:
            if proc in text_lower:
                result["processes"].append({"name": proc, "value": None})

        # Extract known dosage forms
        for form in KNOWN_DOSAGE_FORMS:
            if form in text_lower:
                result["dosage_forms"].append({"name": form, "value": None})

        # Extract comma/plus-separated ingredient candidates
        # Remove known processes and dosage forms from the text before splitting
        cleaned = text_lower
        for proc in KNOWN_PROCESSES:
            cleaned = cleaned.replace(proc, "")
        for form in KNOWN_DOSAGE_FORMS:
            cleaned = cleaned.replace(form, "")
        # Remove ratio patterns
        cleaned = re.sub(r"\b\d+(?:\.\d+)?(?:\s*:\s*\d+(?:\.\d+)?)+\b", "", cleaned)

        # Split on common delimiters
        parts = re.split(r"[,+&;]|\band\b|\bwith\b|\bfor\b|\bके साथ\b|\bऔर\b", cleaned)
        for part in parts:
            part = part.strip().strip(".")
            # Filter out non-ingredient fragments
            if part and len(part) > 1 and len(part) < 60 and not part.isdigit():
                # Check if it looks like an intended use
                use_keywords = [
                    "inflammation", "pain", "healing", "wound", "fever", "digestion",
                    "immunity", "cough", "cold", "diabetes", "arthritis", "skin",
                    "hair", "joint", "stress", "anxiety", "sleep", "weight",
                    "सूजन", "दर्द", "बुखार", "पाचन", "त्वचा", "बालों",
                ]
                is_use = any(kw in part.lower() for kw in use_keywords)
                if is_use:
                    result["intended_uses"].append({"name": part, "value": None})
                else:
                    result["ingredients"].append({"name": part.title(), "value": None})

        return result

    def extract(self, formulation_text: str, language: str = "en") -> StructuredFormulation:
        """Extract structured formulation from free-text description.

        Tries LLM extraction first, falls back to regex heuristics.
        """
        if not formulation_text or not formulation_text.strip():
            return StructuredFormulation(raw_input=formulation_text or "")

        # Try LLM extraction
        extracted_data: Optional[Dict] = None
        try:
            messages = [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": EXTRACTION_USER_PROMPT.format(
                        formulation_text=formulation_text
                    ),
                },
            ]
            raw_response = self._call_llm(messages)
            logger.info(f"Extraction LLM response: {raw_response[:300]}")
            extracted_data = self._parse_llm_json(raw_response)
        except Exception as e:
            logger.warning(f"LLM extraction failed, using regex fallback: {e}")

        # Fallback to regex if LLM failed
        if not extracted_data:
            logger.info("Using regex fallback for formulation extraction.")
            extracted_data = self._regex_fallback(formulation_text)

        # Build StructuredFormulation from parsed data
        def build_elements(items: List, element_type: str) -> List[FormulationElement]:
            elements = []
            for item in (items or []):
                if isinstance(item, dict):
                    name = item.get("name", "").strip()
                    if name:
                        elements.append(
                            FormulationElement(
                                name=name,
                                element_type=element_type,
                                value=item.get("value"),
                                classical_text_ref=item.get("classical_text_ref"),
                            )
                        )
            return elements

        return StructuredFormulation(
            raw_input=formulation_text,
            ingredients=build_elements(extracted_data.get("ingredients", []), "ingredient"),
            ratios=build_elements(extracted_data.get("ratios", []), "ratio"),
            processes=build_elements(extracted_data.get("processes", []), "process"),
            dosage_forms=build_elements(extracted_data.get("dosage_forms", []), "dosage_form"),
            intended_uses=build_elements(extracted_data.get("intended_uses", []), "intended_use"),
        )


def get_default_extractor() -> FormulationExtractor:
    """Returns a singleton-like extractor instance."""
    return FormulationExtractor()
