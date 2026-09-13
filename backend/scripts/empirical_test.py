"""Empirical benchmark script running 12 live queries against local Ollama model."""

import json
import time
from typing import Any, Dict, List
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.generation.generator import get_default_generator
from backend.app.ingestion.chunker import LegalDocumentChunker
from backend.app.ingestion.sample_seed import SAMPLE_DOCUMENTS
from backend.app.main import app
from backend.app.retrieval.service import retrieval_service

# Benchmark query suite
BENCHMARK_QUERIES = [
    # 1. Confident Patents Act Sec 3(p)
    {
        "id": "Q01",
        "category_type": "Confident Retrieval",
        "query_text": "Can I obtain a product patent in India for an unmodified classical turmeric and neem wound formulation described in Charaka Samhita?",
        "jurisdiction": "india",
        "formulation_category": "classical_generic",
        "language": "en",
    },
    # 2. Confident BDA Sec 6 NBA Approval
    {
        "id": "Q02",
        "category_type": "Confident Retrieval",
        "query_text": "Does a foreign company need prior approval from the National Biodiversity Authority before filing a patent based on Indian biological resources?",
        "jurisdiction": "india",
        "formulation_category": "patent_or_proprietary",
        "language": "en",
    },
    # 3. Confident Phytopharmaceutical Rule 122E
    {
        "id": "Q03",
        "category_type": "Confident Retrieval",
        "query_text": "What are the minimum bioactive marker requirements and regulatory standards for a phytopharmaceutical drug under Rule 122E?",
        "jurisdiction": "india",
        "formulation_category": "phytopharmaceutical",
        "language": "en",
    },
    # 4. Confident FSSAI Ayurveda Aahar Sec 5
    {
        "id": "Q04",
        "category_type": "Confident Retrieval",
        "query_text": "Can an Ayurveda Aahar herbal tea or nutritional supplement advertise claims to treat or cure diabetes under FSSAI regulations?",
        "jurisdiction": "india",
        "formulation_category": "ayurveda_aahar_nutraceutical",
        "language": "en",
    },
    # 5. Confident Patents Act Sec 3(e) Synergism
    {
        "id": "Q05",
        "category_type": "Confident Retrieval",
        "query_text": "How can an applicant overcome the Section 3(e) mere admixture bar for a novel proprietary herbal combination?",
        "jurisdiction": "india",
        "formulation_category": "patent_or_proprietary",
        "language": "en",
    },
    # 6. Confident Hindi Query
    {
        "id": "Q06",
        "category_type": "Confident Retrieval (Hindi)",
        "query_text": "क्या चरक संहिता के शास्त्रीय नुस्खे पर धारा 3(p) के तहत भारत में पेटेंट मिल सकता है?",
        "jurisdiction": "india",
        "formulation_category": "classical_generic",
        "language": "hi",
    },
    # 7. Ambiguous / Off-Topic within category (GST Tax)
    {
        "id": "Q07",
        "category_type": "Ambiguous / Low Confidence",
        "query_text": "What is the standard GST corporate tax rebate percentage for exporting Ayurvedic herbs to North America?",
        "jurisdiction": "india",
        "formulation_category": "classical_generic",
        "language": "en",
    },
    # 8. Mismatched Scope (Ayurveda Aahar Clinical Trials)
    {
        "id": "Q08",
        "category_type": "Mismatched Statutory Scope",
        "query_text": "What are the clinical phase III trial sample size guidelines for Ayurveda Aahar products under Indian law?",
        "jurisdiction": "india",
        "formulation_category": "ayurveda_aahar_nutraceutical",
        "language": "en",
    },
    # 9. Out-of-Jurisdiction (Zero Chunks -> Phase 2 Bypass)
    {
        "id": "Q09",
        "category_type": "Out of Jurisdiction",
        "query_text": "What are the unitary patent court requirements for traditional herbal medicines in the European Union?",
        "jurisdiction": "international",
        "formulation_category": "classical_generic",
        "language": "en",
    },
    # 10. Citation Stress Test: Hallucination Bait (Non-existent case law)
    {
        "id": "Q10",
        "category_type": "Citation Stress / Hallucination Bait",
        "query_text": "Under what section of the Patents Act does the landmark Bayer vs AYUSH 2018 judgment grant compulsory licenses for classical herbs?",
        "jurisdiction": "india",
        "formulation_category": "classical_generic",
        "language": "en",
    },
    # 11. Citation Stress Test: Cross-Regime Trap (GI Tag on Phytopharma)
    {
        "id": "Q11",
        "category_type": "Citation Stress / Cross-Regime Trap",
        "query_text": "Is a standardized phytopharmaceutical with 4 bioactive markers eligible for expedited GI tag registration under the Geographical Indications Act?",
        "jurisdiction": "india",
        "formulation_category": "phytopharmaceutical",
        "language": "en",
    },
    # 12. Cosmetic Disease Cure Claims
    {
        "id": "Q12",
        "category_type": "Regulatory Boundary Check",
        "query_text": "Can an Ayurvedic cosmetic skin wash claim to cure severe clinical eczema and psoriasis under Section 3(aaa)?",
        "jurisdiction": "india",
        "formulation_category": "cosmetic",
        "language": "en",
    },
]


def setup_corpus():
    """Populate statutory legal corpus in the retrieval service."""
    chunker = LegalDocumentChunker()
    retriever = retrieval_service.retriever
    retriever.embedder.use_mock = True
    for doc in SAMPLE_DOCUMENTS:
        chunks = chunker.chunk_document(doc)
        retriever.bm25.add_chunks(chunks)
        for c in chunks:
            retriever.register_in_memory_chunk(c.model_dump())


def run_benchmark(model_name: Optional[str] = None):
    import sys
    target_model = model_name or (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            settings.gemini_model
            if settings.gemini_api_key
            else (settings.groq_model if settings.groq_api_key else settings.ollama_model)
        )
    )
    setup_corpus()
    
    # Configure query route generator to use target model
    from backend.app.api.routes import query as query_route
    query_route.generator.model = target_model

    client = TestClient(app)

    print("\n" + "=" * 80, flush=True)
    print(f"RUNNING LIVE EMPIRICAL BENCHMARK (Model: {target_model})", flush=True)
    print("=" * 80 + "\n", flush=True)

    results: List[Dict[str, Any]] = []

    for q in BENCHMARK_QUERIES:
        print(f"--> Testing [{q['id']}] ({q['category_type']}): '{q['query_text'][:60]}...'", flush=True)
        start_time = time.perf_counter()

        response = client.post(
            "/query",
            json={
                "query_text": q["query_text"],
                "jurisdiction": q["jurisdiction"],
                "formulation_category": q["formulation_category"],
                "language": q["language"],
            },
        )
        elapsed = time.perf_counter() - start_time

        data = response.json()
        status_code = response.status_code

        res_record = {
            "id": q["id"],
            "category_type": q["category_type"],
            "query": q["query_text"],
            "model": target_model,
            "status_code": status_code,
            "abstained": data.get("abstained", False),
            "abstention_reason": data.get("abstention_reason"),
            "confidence_score": data.get("confidence_score", 0.0),
            "citations_count": len(data.get("citations", [])),
            "citations": [f"{c['instrument_name']} Sec {c.get('section_number')}" for c in data.get("citations", [])],
            "generation_attempts": data.get("generation_attempts", 0),
            "latency_seconds": round(elapsed, 2),
            "answer_full": data.get("answer") or "",
            "answer_preview": (data.get("answer") or "")[:140].replace("\n", " "),
        }
        results.append(res_record)

        print(
            f"    Result: Abstained={res_record['abstained']} | Conf={res_record['confidence_score']} | "
            f"Attempts={res_record['generation_attempts']} | Latency={res_record['latency_seconds']}s | "
            f"Citations={res_record['citations_count']}",
            flush=True,
        )
        if res_record["answer_preview"]:
            print(f"    Answer: {res_record['answer_preview']}...", flush=True)
        elif res_record["abstention_reason"]:
            print(f"    Abstention Reason: {res_record['abstention_reason'][:90]}...", flush=True)
        print("-" * 80, flush=True)

    # Summary Statistics
    total_queries = len(results)
    successful_answers = [r for r in results if not r["abstained"]]
    abstained_queries = [r for r in results if r["abstained"]]
    
    single_attempt_passes = [r for r in successful_answers if r["generation_attempts"] == 1]
    retried_passes = [r for r in successful_answers if r["generation_attempts"] > 1]
    phase2_bypasses = [r for r in abstained_queries if r["generation_attempts"] == 0]
    terminal_abstentions = [r for r in abstained_queries if r["generation_attempts"] > 0]

    avg_latency_all = sum(r["latency_seconds"] for r in results) / total_queries if total_queries else 0.0
    avg_latency_single = (
        sum(r["latency_seconds"] for r in single_attempt_passes) / len(single_attempt_passes)
        if single_attempt_passes
        else 0.0
    )
    avg_latency_retried = (
        sum(r["latency_seconds"] for r in retried_passes) / len(retried_passes)
        if retried_passes
        else 0.0
    )
    avg_latency_phase2_bypass = (
        sum(r["latency_seconds"] for r in phase2_bypasses) / len(phase2_bypasses)
        if phase2_bypasses
        else 0.0
    )

    print("\n" + "=" * 80, flush=True)
    print(f"EMPIRICAL BENCHMARK SUMMARY REPORT — {target_model}", flush=True)
    print("=" * 80, flush=True)
    print(f"Total Queries Evaluated:            {total_queries}", flush=True)
    print(f"Grounded Answers (Passed):          {len(successful_answers)} / {total_queries} ({len(successful_answers)/total_queries*100:.1f}%)", flush=True)
    print(f"  - First-Attempt Passes (0 retries): {len(single_attempt_passes)}", flush=True)
    print(f"  - Retry Recoveries (1-2 retries):  {len(retried_passes)}", flush=True)
    print(f"Abstained Queries:                  {len(abstained_queries)} / {total_queries} ({len(abstained_queries)/total_queries*100:.1f}%)", flush=True)
    print(f"  - Phase 2 Bypass (0 LLM calls):    {len(phase2_bypasses)}", flush=True)
    print(f"  - Phase 3 Terminal Abstentions:    {len(terminal_abstentions)}", flush=True)
    print("\nLATENCY BENCHMARKS:", flush=True)
    print(f"  - Overall Average Latency:          {avg_latency_all:.2f}s", flush=True)
    print(f"  - First-Attempt Average Latency:    {avg_latency_single:.2f}s", flush=True)
    print(f"  - Retried Queries Average Latency:  {avg_latency_retried:.2f}s", flush=True)
    print(f"  - Phase 2 Bypass Average Latency:   {avg_latency_phase2_bypass:.2f}s (Near instantaneous, 0 tokens)", flush=True)
    print("=" * 80 + "\n", flush=True)

    # Save results to JSON artifact
    slug = target_model.replace(":", "_").replace("/", "_")
    filename = f"empirical_benchmark_{slug}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename}\n", flush=True)


if __name__ == "__main__":
    run_benchmark()
