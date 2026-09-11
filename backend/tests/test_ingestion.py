"""Unit tests for the Legal Document Chunker and Ingestion Pipeline."""

import pytest
from backend.app.ingestion.chunker import LegalDocumentChunker, RawInstrumentDocument
from backend.app.ingestion.embedder import MultilingualEmbedder
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.ingestion.sample_seed import SAMPLE_DOCUMENTS


def test_legal_chunker_sections():
    """Verify that legal documents are chunked by statutory sections rather than fixed tokens."""
    chunker = LegalDocumentChunker()
    patents_doc = SAMPLE_DOCUMENTS[0]  # The Patents Act, 1970

    chunks = chunker.chunk_document(patents_doc)
    assert len(chunks) == 3

    # Verify Section 3(p)
    sec_3p = next((c for c in chunks if c.section_number == "3(p)"), None)
    assert sec_3p is not None
    assert "Traditional Knowledge" in sec_3p.text_content
    assert sec_3p.parent_section_label == "Chapter II — Inventions Not Patentable"
    assert "classical_generic" in sec_3p.formulation_category_relevance
    assert "patent_or_proprietary" in sec_3p.formulation_category_relevance

    # Verify Section 3(d)
    sec_3d = next((c for c in chunks if c.section_number == "3(d)"), None)
    assert sec_3d is not None
    assert "enhancement of the known efficacy" in sec_3d.text_content
    assert "phytopharmaceutical" in sec_3d.formulation_category_relevance


def test_bda_act_chunking():
    """Verify Biological Diversity Act sections are chunked properly."""
    chunker = LegalDocumentChunker()
    bda_doc = SAMPLE_DOCUMENTS[1]

    chunks = chunker.chunk_document(bda_doc)
    assert len(chunks) == 2

    sec_3 = next((c for c in chunks if c.section_number == "3"), None)
    assert sec_3 is not None
    assert "National Biodiversity Authority" in sec_3.text_content

    sec_6 = next((c for c in chunks if c.section_number == "6"), None)
    assert sec_6 is not None
    assert "intellectual property right" in sec_6.text_content


def test_embedder_dynamic_dimensions():
    """Verify embedder dynamically derives vector dimension from model configuration."""
    base_embedder = MultilingualEmbedder(model_name="intfloat/multilingual-e5-base", use_mock=True)
    assert base_embedder.dimension == 768

    large_embedder = MultilingualEmbedder(model_name="intfloat/multilingual-e5-large", use_mock=True)
    assert large_embedder.dimension == 1024


def test_embedder_passage_and_query_encoding():
    """Verify passages and queries produce vectors of correct dimension."""
    embedder = MultilingualEmbedder(model_name="intfloat/multilingual-e5-base", use_mock=True)
    passages = ["Section 3(p) Traditional Knowledge bar", "Section 6 NBA approval"]
    vectors = embedder.embed_passages(passages)

    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768

    query_vec = embedder.embed_query("Can I patent an Ayurvedic turmeric formula?")
    assert len(query_vec) == 768


def test_ingestion_pipeline_batch_simulation():
    """Test full ingestion pipeline without live Qdrant/Supabase connection."""
    embedder = MultilingualEmbedder(model_name="intfloat/multilingual-e5-base", use_mock=True)
    pipeline = IngestionPipeline(embedder=embedder)
    results = pipeline.ingest_batch(SAMPLE_DOCUMENTS[:2])

    assert len(results) == 2
    assert results[0]["instrument_name"] == "The Patents Act, 1970"
    assert results[0]["chunks_count"] == 3
    assert results[0]["vector_dimension"] == 768
    assert len(results[0]["chunk_ids"]) == 3

    assert results[1]["instrument_name"] == "The Biological Diversity Act, 2002"
    assert results[1]["chunks_count"] == 2
