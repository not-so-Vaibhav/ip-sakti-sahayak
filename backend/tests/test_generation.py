"""Unit and Integration tests for Citation-Constrained Generation (/query)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.generation.generator import CitationConstrainedGenerator
from backend.app.generation.models import CitationItem, QueryRequest, QueryResponse
from backend.app.main import app
from backend.app.retrieval.models import RetrievedChunk
from backend.app.retrieval.service import retrieval_service
from backend.app.ingestion.chunker import LegalDocumentChunker
from backend.app.ingestion.sample_seed import SAMPLE_DOCUMENTS


@pytest.fixture(autouse=True)
def populate_sample_corpus():
    """Ensure the in-memory retriever has the sample statutory corpus loaded."""
    chunker = LegalDocumentChunker()
    retriever = retrieval_service.retriever
    retriever.embedder.use_mock = True
    for doc in SAMPLE_DOCUMENTS:
        chunks = chunker.chunk_document(doc)
        retriever.bm25.add_chunks(chunks)
        for c in chunks:
            retriever.register_in_memory_chunk(c.model_dump())


def test_citation_validation_success():
    """Verify that correctly cited short chunk IDs pass validation."""
    generator = CitationConstrainedGenerator()
    allowed = {"chunk-1", "chunk-2"}

    text = "Section 3(p) prohibits traditional knowledge [cite:chunk-1]. Rule 122E requires clinical markers [cite:chunk-2]."
    is_valid, valid_ids, invalid_ids, _ = generator.validate_citations(text, allowed)

    assert is_valid is True
    assert valid_ids == ["chunk-1", "chunk-2"]
    assert len(invalid_ids) == 0


def test_citation_validation_relaxed_syntax_variants():
    """Verify that round brackets (cite:chunk-1) and bare cite:chunk-2 are accepted."""
    generator = CitationConstrainedGenerator()
    allowed = {"chunk-1", "chunk-2", "chunk-3"}

    text = "Synergism must be demonstrated (cite:chunk-1). BDA requires prior approval cite:chunk-2 and [cite:chunk-3]."
    is_valid, valid_ids, invalid_ids, _ = generator.validate_citations(text, allowed)

    assert is_valid is True
    assert valid_ids == ["chunk-1", "chunk-2", "chunk-3"]
    assert len(invalid_ids) == 0


def test_citation_validation_partial_hallucination_rejects_whole_answer():
    """
    CRITICAL CONSTRAINT: If an answer contains 1 valid citation and 1 hallucinated/unretrieved citation,
    the ENTIRE answer must be rejected.
    """
    generator = CitationConstrainedGenerator()
    allowed = {"chunk-1"}

    text = "Valid claim [cite:chunk-1]. Hallucinated claim [cite:chunk-99]."
    is_valid, valid_ids, invalid_ids, _ = generator.validate_citations(text, allowed)

    assert is_valid is False
    assert valid_ids == ["chunk-1"]
    assert invalid_ids == ["chunk-99"]


def test_citation_validation_missing_citations_rejects():
    """Ungrounded text without citation markers is rejected."""
    generator = CitationConstrainedGenerator()
    allowed = {"chunk-1"}
    text = "You cannot patent this formulation because of general knowledge principles."
    is_valid, valid_ids, invalid_ids, _ = generator.validate_citations(text, allowed)

    assert is_valid is False
    assert len(valid_ids) == 0


def test_multi_turn_retry_recovery():
    """Simulate retry recovery: Attempt 1 fails validation with bad ID, Attempt 2 corrects and succeeds."""
    valid_uuid = "11111111-1111-1111-1111-111111111111"
    fake_id = "chunk-99"

    call_count = 0

    def mock_llm_recovering(messages):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First turn: bad citation
            return f"Under Section 3(p), traditional Ayurvedic formulations are barred [cite:{fake_id}]."
        else:
            # Second turn (after correction message): corrected short citation
            return "Under Section 3(p), traditional Ayurvedic formulations are barred [cite:chunk-1]."

    generator = CitationConstrainedGenerator(llm_callable=mock_llm_recovering, max_retries=2)

    chunks = [
        RetrievedChunk(
            chunk_id=valid_uuid,
            instrument_name="The Patents Act, 1970",
            section_number="3(p)",
            jurisdiction="india",
            regime_category="patent",
            authority_level="primary_law",
            text_content="Section 3(p) traditional knowledge bar",
            source_url="http://patents",
            combined_score=0.88,
        )
    ]

    answer, citations, abstained, reason, attempts = generator.generate_answer(
        query_text="Can I patent a classical formula?",
        jurisdiction="india",
        formulation_category="classical_generic",
        retrieved_chunks=chunks,
    )

    assert abstained is False
    assert attempts == 2
    assert len(citations) == 1
    # MUST resolve to real UUID in CitationItem, NOT "chunk-1"
    assert citations[0].chunk_id == valid_uuid
    assert "[^1]" in answer
    assert "[cite:chunk-1]" not in answer


def test_request_scoped_short_id_isolation_and_no_leakage():
    """
    CRITICAL REQUIREMENT 5: Request-scoped short-ID mapping must NOT leak or collide across sequential queries.
    Even if Query 1 and Query 2 share chunks in different positions, each must resolve cleanly to the correct real UUID.
    """
    uuid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # Patents Act Sec 3(p)
    uuid_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # BDA Sec 6
    uuid_c = "cccccccc-cccc-cccc-cccc-cccccccccccc"  # D&C Rule 122E

    chunk_a = RetrievedChunk(
        chunk_id=uuid_a, instrument_name="Patents Act", section_number="3(p)",
        jurisdiction="india", regime_category="patent", authority_level="primary_law",
        text_content="Sec 3(p)", source_url="http://a", combined_score=0.9
    )
    chunk_b = RetrievedChunk(
        chunk_id=uuid_b, instrument_name="BDA", section_number="6",
        jurisdiction="india", regime_category="biodiversity", authority_level="primary_law",
        text_content="Sec 6", source_url="http://b", combined_score=0.8
    )
    chunk_c = RetrievedChunk(
        chunk_id=uuid_c, instrument_name="D&C Act", section_number="122E",
        jurisdiction="india", regime_category="pharma", authority_level="rules",
        text_content="Rule 122E", source_url="http://c", combined_score=0.85
    )

    # Query 1 receives [chunk_a (becomes chunk-1), chunk_b (becomes chunk-2)]
    def mock_llm_query1(messages):
        # Asserts prompt provided chunk-1 and chunk-2
        prompt_content = messages[1]["content"]
        assert '<chunk id="chunk-1">' in prompt_content
        assert '<chunk id="chunk-2">' in prompt_content
        return "Query 1 relies on Patents Act [cite:chunk-1] and BDA [cite:chunk-2]."

    gen1 = CitationConstrainedGenerator(llm_callable=mock_llm_query1)
    ans1, cites1, abs1, _, att1 = gen1.generate_answer(
        query_text="Query 1", jurisdiction="india", formulation_category="classical_generic",
        retrieved_chunks=[chunk_a, chunk_b]
    )
    assert abs1 is False
    assert len(cites1) == 2
    assert cites1[0].chunk_id == uuid_a  # chunk-1 resolved to uuid_a
    assert cites1[1].chunk_id == uuid_b  # chunk-2 resolved to uuid_b

    # Query 2 receives [chunk_c (becomes chunk-1), chunk_a (becomes chunk-2)]
    def mock_llm_query2(messages):
        # Asserts prompt provided chunk-1 and chunk-2 with chunk_a now at chunk-2
        prompt_content = messages[1]["content"]
        assert '<chunk id="chunk-1">' in prompt_content
        assert '<chunk id="chunk-2">' in prompt_content
        return "Query 2 relies on D&C Rule 122E [cite:chunk-1] and Patents Act [cite:chunk-2]."

    gen2 = CitationConstrainedGenerator(llm_callable=mock_llm_query2)
    ans2, cites2, abs2, _, att2 = gen2.generate_answer(
        query_text="Query 2", jurisdiction="india", formulation_category="phytopharmaceutical",
        retrieved_chunks=[chunk_c, chunk_a]
    )
    assert abs2 is False
    assert len(cites2) == 2
    assert cites2[0].chunk_id == uuid_c  # chunk-1 resolved to uuid_c
    assert cites2[1].chunk_id == uuid_a  # chunk-2 resolved to uuid_a (no collision with Query 1!)


def test_terminal_fallback_abstention_on_persistent_failure():
    """When all retries fail citation validation, system must force terminal abstention."""
    fake_id = "99999999-9999-9999-9999-999999999999"

    def mock_llm_always_fails(messages):
        return f"Hallucinated answer [cite:{fake_id}]."

    generator = CitationConstrainedGenerator(llm_callable=mock_llm_always_fails, max_retries=2)
    valid_id = "11111111-1111-1111-1111-111111111111"

    chunks = [
        RetrievedChunk(
            chunk_id=valid_id,
            instrument_name="The Patents Act, 1970",
            section_number="3(p)",
            jurisdiction="india",
            regime_category="patent",
            authority_level="primary_law",
            text_content="Section 3(p) traditional knowledge bar",
            source_url="http://patents",
            combined_score=0.85,
        )
    ]

    answer, citations, abstained, reason, attempts = generator.generate_answer(
        query_text="Can I patent a classical formula?",
        jurisdiction="india",
        formulation_category="classical_generic",
        retrieved_chunks=chunks,
    )

    assert abstained is True
    assert answer is None
    assert len(citations) == 0
    assert attempts == 3  # Initial attempt + 2 retries
    assert "Unable to verify strict citation grounding" in reason


def test_end_to_end_query_endpoint_success(monkeypatch):
    """Test full /query API endpoint execution with grounded generation."""
    client = TestClient(app)

    def mock_generate(query_text, jurisdiction, formulation_category, retrieved_chunks, language="en", confidence_score=0.8):
        top_chunk = retrieved_chunks[0]
        answer = f"According to Section 3(p) of the Patents Act, 1970, unmodified traditional knowledge is excluded from patentability [^1]."
        citations = [
            CitationItem(
                chunk_id=top_chunk.chunk_id,
                instrument_name=top_chunk.instrument_name,
                section_number=top_chunk.section_number,
                parent_section_label=top_chunk.parent_section_label,
                authority_level=top_chunk.authority_level,
                source_url=top_chunk.source_url,
                text_snippet=top_chunk.text_content[:150],
                rank_position=1,
                retrieval_score=top_chunk.combined_score,
            )
        ]
        return answer, citations, False, None, 1

    monkeypatch.setattr("backend.app.api.routes.query.generator.generate_answer", mock_generate)

    response = client.post(
        "/query",
        json={
            "query_text": "Can I patent a classical turmeric formulation under Section 3(p)?",
            "jurisdiction": "india",
            "formulation_category": "classical_generic",
            "language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["abstained"] is False
    assert data["confidence_score"] >= 0.50
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["section_number"] == "3(p)"
    assert "[^1]" in data["answer"]


def test_end_to_end_query_endpoint_phase2_abstention_bypass(monkeypatch):
    """Out-of-domain queries that Phase 2 abstains on must bypass LLM call and return abstention response."""
    client = TestClient(app)

    llm_called = False

    def mock_generate_should_not_be_called(*args, **kwargs):
        nonlocal llm_called
        llm_called = True
        return "Should never be called", [], False, None, 1

    monkeypatch.setattr("backend.app.api.routes.query.generator.generate_answer", mock_generate_should_not_be_called)

    # Query international jurisdiction (no docs ingested -> 0 chunks -> Phase 2 abstain)
    response = client.post(
        "/query",
        json={
            "query_text": "What is the European patent directive on traditional medicine?",
            "jurisdiction": "international",
            "formulation_category": "classical_generic",
            "language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["abstained"] is True
    assert data["escalation_offered"] is True
    assert data["answer"] is None
    assert len(data["citations"]) == 0
    assert data["generation_attempts"] == 0
    assert llm_called is False  # Confirms LLM was never called!


def test_end_to_end_query_endpoint_phase2_low_confidence_bypass(monkeypatch):
    """
    CRITICAL REGRESSION TEST: Queries with retrieval confidence below the configured threshold (0.50)
    MUST immediately bypass the generation layer with 0 LLM calls.
    """
    from backend.app.retrieval.models import RetrievalResult
    client = TestClient(app)

    llm_called = False

    def mock_generate_should_not_be_called(*args, **kwargs):
        nonlocal llm_called
        llm_called = True
        return "Should never be called", [], False, None, 1

    def mock_low_confidence_retrieval(*args, **kwargs):
        return RetrievalResult(
            query_text="Ambiguous query",
            jurisdiction="india",
            formulation_category="classical_generic",
            language="en",
            chunks=[],
            confidence_score=0.349,
            abstained=True,
            abstention_reason="Retrieval confidence score (0.349) is below the minimum threshold (0.50).",
            corroborating_chunks_count=0,
            top_score=0.349,
        )

    monkeypatch.setattr("backend.app.api.routes.query.generator.generate_answer", mock_generate_should_not_be_called)
    monkeypatch.setattr("backend.app.api.routes.query.retrieval_service.retrieve", mock_low_confidence_retrieval)

    response = client.post(
        "/query",
        json={
            "query_text": "What is the GST rebate for exporting herbs?",
            "jurisdiction": "india",
            "formulation_category": "classical_generic",
            "language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["abstained"] is True
    assert data["confidence_score"] == 0.349
    assert data["escalation_offered"] is True
    assert data["answer"] is None
    assert len(data["citations"]) == 0
    assert data["generation_attempts"] == 0
    assert llm_called is False  # Explicitly asserts LLM client was NEVER invoked


def test_generation_timeout_forced_abstention(monkeypatch):
    """Test that an httpx.TimeoutException during generation triggers graceful forced abstention."""
    import httpx
    from backend.app.generation.generator import CitationConstrainedGenerator
    from backend.app.retrieval.models import RetrievedChunk

    def mock_timeout_llm(*args, **kwargs):
        raise httpx.ReadTimeout("Read timed out from LLM endpoint")

    gen = CitationConstrainedGenerator(llm_callable=mock_timeout_llm)
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-test-id",
            instrument_name="The Patents Act, 1970",
            section_number="3(p)",
            jurisdiction="india",
            regime_category="patent",
            authority_level="primary_law",
            text_content="Section 3(p) traditional knowledge bar",
            source_url="http://patents",
            combined_score=0.85,
        )
    ]

    answer, citations, abstained, reason, attempts = gen.generate_answer(
        query_text="Can I patent a classical formula?",
        jurisdiction="india",
        formulation_category="classical_generic",
        retrieved_chunks=chunks,
    )

    assert abstained is True
    assert answer is None
    assert len(citations) == 0
    assert "timed out" in reason.lower()

