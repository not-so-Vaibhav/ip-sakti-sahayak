"""Legal Section and Article Chunker for IP-SAKTI Sahayak.

Chunks legal and regulatory documents by statutory section/clause/article rather than
arbitrary token windows, preserving hierarchical legal context.
"""

import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SectionChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: Optional[str] = None
    instrument_name: str
    jurisdiction: str
    regime_category: str
    authority_level: str
    section_number: Optional[str] = None
    parent_section_label: Optional[str] = None
    text_content: str
    language: str = "en"
    formulation_category_relevance: List[str] = Field(default_factory=list)
    source_url: str
    effective_date: Optional[str] = None
    last_amended_date: Optional[str] = None


class RawInstrumentDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instrument_name: str
    jurisdiction: str = "india"
    regime_category: str
    authority_level: str = "primary_law"
    source_url: str
    effective_date: Optional[str] = None
    last_amended_date: Optional[str] = None
    default_formulation_relevance: List[str] = Field(default_factory=list)
    language: str = "en"
    raw_content: str


class LegalDocumentChunker:
    """Parses legal instruments by chapters, sections, rules, and articles."""

    # Regex patterns for detecting legal divisions
    CHAPTER_PATTERN = re.compile(
        r"^(?:#+\s*)?(?:CHAPTER|PART|अध्याय|भाग)\s+([IVXLCDM0-9]+)[\s:—–-]+([^\n]+)",
        re.IGNORECASE | re.MULTILINE,
    )
    SECTION_HEADER_PATTERN = re.compile(
        r"^(?:#+\s*)?(?:Section|Sec\.|Article|Art\.|Rule|धारा|नियम)\s+([0-9]+[A-Za-z]?(?:\([a-z0-9]+\))?)[\s:—–.-]+([^\n]*)",
        re.IGNORECASE | re.MULTILINE,
    )

    def chunk_document(self, doc: RawInstrumentDocument) -> List[SectionChunk]:
        """Chunk a document into statutory section blocks."""
        chunks: List[SectionChunk] = []
        raw_text = doc.raw_content.strip()

        # Split into blocks based on markdown headers or section markers
        lines = raw_text.split("\n")
        current_chapter: Optional[str] = None
        current_section: Optional[str] = None
        current_text_lines: List[str] = []
        current_relevance: List[str] = list(doc.default_formulation_relevance)

        def flush_current():
            nonlocal current_text_lines, current_section, current_chapter, current_relevance
            if current_text_lines:
                content = "\n".join(current_text_lines).strip()
                if content:
                    # Clean tags like [relevance: classical_generic, patent_or_proprietary]
                    relevance_match = re.search(r"\[relevance:\s*([^\]]+)\]", content, re.IGNORECASE)
                    section_relevance = list(current_relevance)
                    if relevance_match:
                        tags = [t.strip().lower() for t in relevance_match.group(1).split(",")]
                        section_relevance = list(set(section_relevance + tags))
                        content = re.sub(r"\[relevance:\s*[^\]]+\]", "", content, flags=re.IGNORECASE).strip()

                    chunks.append(
                        SectionChunk(
                            document_id=doc.id,
                            instrument_name=doc.instrument_name,
                            jurisdiction=doc.jurisdiction,
                            regime_category=doc.regime_category,
                            authority_level=doc.authority_level,
                            section_number=current_section,
                            parent_section_label=current_chapter,
                            text_content=content,
                            language=doc.language,
                            formulation_category_relevance=section_relevance,
                            source_url=doc.source_url,
                            effective_date=doc.effective_date,
                            last_amended_date=doc.last_amended_date,
                        )
                    )
            current_text_lines = []

        for line in lines:
            stripped = line.strip()

            # Check for chapter header
            chapter_match = self.CHAPTER_PATTERN.match(stripped)
            if chapter_match:
                flush_current()
                current_chapter = f"Chapter {chapter_match.group(1)} — {chapter_match.group(2).strip()}"
                continue

            # Check for section header
            section_match = self.SECTION_HEADER_PATTERN.match(stripped)
            if section_match:
                flush_current()
                sec_num = section_match.group(1).strip()
                sec_title = section_match.group(2).strip()
                current_section = sec_num
                if sec_title:
                    current_text_lines.append(f"Section {sec_num}: {sec_title}")
                else:
                    current_text_lines.append(f"Section {sec_num}")
                continue

            # Markdown H2/H3 as fallback section delimiter if no explicit 'Section' keyword
            if stripped.startswith("## ") and not current_section:
                flush_current()
                current_section = stripped.replace("##", "").strip()
                continue

            current_text_lines.append(line)

        flush_current()

        # Fallback if no sections were detected: treat full document as one single chunk
        if not chunks and raw_text:
            chunks.append(
                SectionChunk(
                    document_id=doc.id,
                    instrument_name=doc.instrument_name,
                    jurisdiction=doc.jurisdiction,
                    regime_category=doc.regime_category,
                    authority_level=doc.authority_level,
                    section_number="General",
                    parent_section_label=None,
                    text_content=raw_text,
                    language=doc.language,
                    formulation_category_relevance=doc.default_formulation_relevance,
                    source_url=doc.source_url,
                    effective_date=doc.effective_date,
                    last_amended_date=doc.last_amended_date,
                )
            )

        return chunks
