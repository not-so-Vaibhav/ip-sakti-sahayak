"""Unit and Integration Tests for Hybrid Retrieval, BM25 Indexing, Confidence Scoring, and Abstention.

Tests against the real sample statutory legal corpus (Patents Act 1970, BDA 2002, D&C Act 1940, FSSAI 2022).
"""

import pytest
from backend.app.ingestion.chunker import LegalDocumentChunker, RawInstrumentDocument
from backend.app.ingestion.embedder import MultilingualEmbedder
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.ingestion.sample_seed import SAMPLE_DOCUMENTS
from backend.app.retrieval.bm25 import BM25Index
from backend.app.retrieval.confidence import ConfidenceEvaluator, evaluate_retrieval_confidence
from backend.app.retrieval.hybrid import HybridRetriever
from backend.app.retrieval.models import RetrievalQuery, RetrievedChunk


@pytest.fixture
def populated_retriever():
    """Builds a fresh HybridRetriever and ingests the full real sample legal corpus."""
    bm25 = BM25Index()
    embedder = MultilingualEmbedder(model_name="intfloat/multilingual-e5-base", use_mock=True)
    chunker = LegalDocumentChunker()
    retriever = HybridRetriever(embedder=embedder, sparse_index=bm25, dense_weight=0.6, sparse_weight=0.4)

    # Ingest sample statutory documents into the retriever
    for doc in SAMPLE_DOCUMENTS:
        chunks = chunker.chunk_document(doc)
        bm25.add_chunks(chunks)
        for chunk in chunks:
            retriever.register_in_memory_chunk(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": doc.id,
                    "instrument_name": chunk.instrument_name,
                    "jurisdiction": chunk.jurisdiction,
                    "regime_category": chunk.regime_category,
                    "authority_level": chunk.authority_level,
                    "section_number": chunk.section_number,
                    "parent_section_label": chunk.parent_section_label,
                    "text_content": chunk.text_content,
                    "language": chunk.language,
                    "source_url": chunk.source_url,
                    "formulation_category_relevance": chunk.formulation_category_relevance,
                }
            )

    return retriever


def test_confident_patents_act_3p_retrieval(populated_retriever):
    """Query on classical Ayurvedic formula patent bar should retrieve Patents Act Sec 3(p) with high confidence."""
    query = RetrievalQuery(
        query_text="Can I patent a classical turmeric formulation unmodified from First Schedule text under Section 3(p)?",
        jurisdiction="india",
        formulation_category="classical_generic",
        top_k=3,
    )
    result = populated_retriever.retrieve(query)

    assert result.abstained is False
    assert result.confidence_score >= 0.50
    assert len(result.chunks) >= 1

    top_chunk = result.chunks[0]
    assert top_chunk.instrument_name == "The Patents Act, 1970"
    assert top_chunk.section_number == "3(p)"
    assert "Traditional Knowledge" in top_chunk.text_content
    assert top_chunk.combined_score > 0.60


def test_confident_bda_section_6_retrieval(populated_retriever):
    """Query on NBA approval for foreign companies/IP should retrieve BDA Sec 3 and Sec 6."""
    query = RetrievalQuery(
        query_text="Do foreign entities need NBA approval before filing patent application under Section 6?",
        jurisdiction="india",
        formulation_category="patent_or_proprietary",
        top_k=3,
    )
    result = populated_retriever.retrieve(query)

    assert result.abstained is False
    assert result.confidence_score >= 0.50

    sec_numbers = [c.section_number for c in result.chunks]
    assert "6" in sec_numbers or "3" in sec_numbers
    bda_chunk = next(c for c in result.chunks if c.instrument_name == "The Biological Diversity Act, 2002")
    assert bda_chunk is not None


def test_confident_phytopharmaceutical_rule_122e(populated_retriever):
    """Query on standardized 4-marker plant extract should retrieve Rule 122E."""
    query = RetrievalQuery(
        query_text="What are the clinical trial and bioactive marker standards for phytopharmaceutical drugs under Rule 122E?",
        jurisdiction="india",
        formulation_category="phytopharmaceutical",
        top_k=3,
    )
    result = populated_retriever.retrieve(query)

    assert result.abstained is False
    top_chunk = result.chunks[0]
    assert top_chunk.section_number == "122E" or "Rule 122E" in top_chunk.text_content
    assert "four bioactive" in top_chunk.text_content.lower()


def test_confident_ayurveda_aahar_fssai_labeling(populated_retriever):
    """Query on Ayurveda Aahar disease cure claims prohibition should retrieve FSSAI Regulations Section 5."""
    query = RetrievalQuery(
        query_text="Can Ayurveda Aahar products make disease cure claims on package labels under Section 5?",
        jurisdiction="india",
        formulation_category="ayurveda_aahar_nutraceutical",
        top_k=3,
    )
    result = populated_retriever.retrieve(query)

    assert result.abstained is False
    top_chunk = result.chunks[0]
    assert top_chunk.instrument_name == "Food Safety and Standards (Ayurveda Aahar) Regulations, 2022"
    assert "cure" in top_chunk.text_content.lower()


def test_hard_metadata_prefilter_isolation(populated_retriever):
    """Chunks not matching formulation_category_relevance must NEVER appear in results, even with keyword match."""
    # Section 3(p) exists in Patents Act, but Patents Act is not relevant to 'ayurveda_aahar_nutraceutical'
    query = RetrievalQuery(
        query_text="Section 3(p) traditional knowledge bar",
        jurisdiction="india",
        formulation_category="ayurveda_aahar_nutraceutical",
        top_k=5,
    )
    result = populated_retriever.retrieve(query)

    # Must only return Ayurveda Aahar chunks, never Patents Act Sec 3(p)
    for chunk in result.chunks:
        assert chunk.instrument_name != "The Patents Act, 1970"
        assert "ayurveda_aahar_nutraceutical" in chunk.formulation_category_relevance


def test_out_of_jurisdiction_zero_chunks_abstention(populated_retriever):
    """Querying a jurisdiction with no ingested documents must immediately abstain with 0 confidence."""
    query = RetrievalQuery(
        query_text="What is the European Patent Office bar on traditional medicine formulations?",
        jurisdiction="international",
        formulation_category="classical_generic",
        top_k=5,
    )
    result = populated_retriever.retrieve(query)

    assert result.abstained is True
    assert result.confidence_score == 0.0
    assert len(result.chunks) == 0
    assert result.abstention_reason is not None
    assert "international" in result.abstention_reason.lower()


def test_ambiguous_out_of_domain_query_abstention(populated_retriever):
    """Out-of-domain queries with low retrieval scores must trigger abstention (confidence < 0.50)."""
    # Create an evaluator with threshold 0.50
    evaluator = ConfidenceEvaluator(threshold=0.50, corroboration_floor=0.45)

    # Low score chunks simulating unrelated query
    low_chunks = [
        RetrievedChunk(
            chunk_id="chk-1",
            instrument_name="The Patents Act, 1970",
            jurisdiction="india",
            regime_category="patent",
            authority_level="primary_law",
            text_content="Section 3(p) traditional knowledge",
            source_url="http://test",
            combined_score=0.28,
        )
    ]
    confidence, abstained, reason, corroborating, top_score = evaluator.evaluate(low_chunks)

    assert abstained is True
    assert confidence < 0.50
    assert "below the minimum threshold" in reason


def test_confidence_corroboration_penalty():
    """Single-source results receive a corroboration penalty factor compared to multiple corroborating sources."""
    evaluator = ConfidenceEvaluator(threshold=0.50, corroboration_floor=0.45)

    # Case 1: 2 corroborating sources >= 0.45
    multi_chunks = [
        RetrievedChunk(chunk_id="c1", instrument_name="Act 1", jurisdiction="india", regime_category="patent", authority_level="primary_law", text_content="t1", source_url="u1", combined_score=0.75),
        RetrievedChunk(chunk_id="c2", instrument_name="Act 2", jurisdiction="india", regime_category="patent", authority_level="primary_law", text_content="t2", source_url="u2", combined_score=0.65),
    ]
    conf_multi, abstained_multi, _, corr_multi, _ = evaluator.evaluate(multi_chunks)
    assert abstained_multi is False
    assert corr_multi == 2
    assert conf_multi == 0.75

    # Case 2: Only 1 corroborating source >= 0.45
    single_chunks = [
        RetrievedChunk(chunk_id="c1", instrument_name="Act 1", jurisdiction="india", regime_category="patent", authority_level="primary_law", text_content="t1", source_url="u1", combined_score=0.75),
        RetrievedChunk(chunk_id="c2", instrument_name="Act 2", jurisdiction="india", regime_category="patent", authority_level="primary_law", text_content="t2", source_url="u2", combined_score=0.20),
    ]
    conf_single, abstained_single, _, corr_single, _ = evaluator.evaluate(single_chunks)
    assert corr_single == 1
    assert conf_single == round(0.75 * 0.85, 3)  # Single source penalty


def test_tunable_weights_impact(populated_retriever):
    """Verify that dense vs sparse weights alter ranking and scores dynamically."""
    query = RetrievalQuery(
        query_text="Section 3(p) traditional knowledge",
        jurisdiction="india",
        formulation_category="classical_generic",
        top_k=3,
    )

    # Pure sparse retriever (100% BM25 keyword matching)
    sparse_only_retriever = HybridRetriever(
        embedder=populated_retriever.embedder,
        sparse_index=populated_retriever.bm25,
        dense_weight=0.0,
        sparse_weight=1.0,
    )
    for cid, data in populated_retriever._in_memory_corpus.items():
        sparse_only_retriever.register_in_memory_chunk(data)

    res_sparse = sparse_only_retriever.retrieve(query)
    assert res_sparse.chunks[0].section_number == "3(p)"
    assert res_sparse.chunks[0].combined_score == res_sparse.chunks[0].sparse_score


def test_dynamic_ingestion_refresh_hook():
    """Verify newly ingested documents are automatically added to BM25 and searchable immediately."""
    bm25 = BM25Index()
    embedder = MultilingualEmbedder(use_mock=True)
    pipeline = IngestionPipeline(embedder=embedder, sparse_index=bm25)

    new_doc = RawInstrumentDocument(
        instrument_name="National AYUSH Policy 2026",
        jurisdiction="india",
        regime_category="drug_regulatory",
        authority_level="institutional_guidance",
        source_url="https://ayush.gov.in/policy2026.pdf",
        default_formulation_relevance=["classical_generic"],
        language="en",
        raw_content="""
CHAPTER I — Policy Objectives

Section 10 — Standardized TKDL Defense Protocol
The National AYUSH Mission establishes an expedited TKDL defense portal for state drug licensing authorities.
[relevance: classical_generic]
""",
    )

    # Ingest document through pipeline
    res = pipeline.ingest_document(new_doc, sync_to_qdrant=False, sync_to_supabase=False)
    assert res["chunks_count"] == 1

    # Search BM25 directly to verify automatic index update
    search_hits = bm25.search("TKDL Defense Protocol")
    assert len(search_hits) >= 1
    hit_chunk_id = list(search_hits.keys())[0]
    assert search_hits[hit_chunk_id] > 0.0


def test_hindi_query_retrieval(populated_retriever):
    """Verify Hindi legal queries retrieve applicable sections under metadata pre-filters."""
    query = RetrievalQuery(
        query_text="पारंपरिक ज्ञान और हल्दी आधारित फॉर्मूलेशन पर पेटेंट प्रतिबंध धारा 3(p)",
        jurisdiction="india",
        formulation_category="classical_generic",
        language="hi",
        top_k=3,
    )
    result = populated_retriever.retrieve(query)
    assert result.abstained is False
    assert len(result.chunks) >= 1
    assert result.language == "hi"
    # Section 3(p) extracted from query clause
    sec_numbers = [c.section_number for c in result.chunks]
    assert "3(p)" in sec_numbers
