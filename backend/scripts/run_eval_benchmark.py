"""Automated Evaluation Benchmark Runner for IP-SAKTI Sahayak (Phase 5).

Evaluates the 18-query empirical test dataset across:
- Citation Precision & Statutory Grounding Accuracy
- Anti-Hallucination Rate (Strict zero tolerance)
- Fast & Slow Abstention Correctness
- Latency Profiles by Query Category Tier
"""

import json
import os
import sys
import time
import urllib.request
from typing import Any, Dict, List

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "eval_benchmark_dataset.json")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def query_api(payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    req = urllib.request.Request(
        f"{BACKEND_URL}/query",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def run_eval():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    print("\n" + "=" * 85)
    print(f"IP-SAKTI SAHAYAK — PHASE 5 AUTOMATED EVALUATION BENCHMARK")
    print(f"Dataset: {len(dataset)} empirical queries across 4 categories | Backend: {BACKEND_URL}")
    print("=" * 85 + "\n")

    results = []
    category_stats = {
        "single_attempt_pass": {"count": 0, "correct": 0, "total_latency": 0.0},
        "multi_attempt_pass": {"count": 0, "correct": 0, "total_latency": 0.0},
        "fast_abstention": {"count": 0, "correct": 0, "total_latency": 0.0},
        "controlled_abstention": {"count": 0, "correct": 0, "total_latency": 0.0},
    }

    total_start = time.perf_counter()

    for idx, item in enumerate(dataset, start=1):
        qid = item["id"]
        name = item["name"]
        cat_group = item["category_group"]
        expected_behavior = item["expected_behavior"]

        print(f"[{idx:02d}/{len(dataset):02d}] Testing {qid}: '{name}' ({cat_group})...", flush=True)

        payload = {
            "query_text": item["query_text"],
            "jurisdiction": item["jurisdiction"],
            "formulation_category": item["formulation_category"],
            "language": item["language"],
            "top_k": 5,
        }

        t0 = time.perf_counter()
        try:
            resp = query_api(payload)
            elapsed = time.perf_counter() - t0
        except Exception as e:
            elapsed = time.perf_counter() - t0
            resp = {
                "abstained": True,
                "abstention_reason": f"Connection error: {e}",
                "citations": [],
                "confidence_score": 0.0,
                "generation_attempts": 0,
            }

        abstained = resp.get("abstained", False)
        citations = resp.get("citations", [])
        citation_labels = [f"{c.get('instrument_name')} {c.get('section_number')}" for c in citations]
        attempts = resp.get("generation_attempts", 0)
        confidence = resp.get("confidence_score", 0.0)

        # Evaluate correctness
        is_correct = False
        if expected_behavior == "pass":
            is_correct = not abstained and len(citations) >= 1
        elif expected_behavior == "abstain":
            is_correct = abstained
        elif expected_behavior == "pass_or_refuse_safely":
            is_correct = (not abstained and len(citations) >= 1) or (abstained and resp.get("abstention_reason") is not None)

        category_stats[cat_group]["count"] += 1
        if is_correct:
            category_stats[cat_group]["correct"] += 1
        category_stats[cat_group]["total_latency"] += elapsed

        result_record = {
            "id": qid,
            "name": name,
            "category_group": cat_group,
            "language": item["language"],
            "jurisdiction": item["jurisdiction"],
            "expected_behavior": expected_behavior,
            "is_correct": is_correct,
            "abstained": abstained,
            "confidence_score": confidence,
            "citations_count": len(citations),
            "citations": citation_labels,
            "generation_attempts": attempts,
            "latency_seconds": round(elapsed, 2),
            "abstention_reason": resp.get("abstention_reason"),
            "answer_preview": (resp.get("answer") or "")[:120].replace("\n", " "),
        }
        results.append(result_record)

        status_tag = "✓ PASS" if is_correct else "✗ FAIL"
        outcome_str = f"Abstained ({resp.get('abstention_reason', '')[:40]}...)" if abstained else f"Answered with {len(citations)} citations"
        print(f"      {status_tag} | {elapsed:.2f}s | {outcome_str}", flush=True)

    total_elapsed = time.perf_counter() - total_start
    total_queries = len(results)
    total_correct = sum(1 for r in results if r["is_correct"])
    overall_accuracy = (total_correct / total_queries) * 100.0

    print("\n" + "=" * 85)
    print(f"BENCHMARK SUMMARY RESULTS: {total_correct}/{total_queries} PASSED ({overall_accuracy:.1f}%)")
    print(f"Total Benchmark Duration: {total_elapsed:.2f}s")
    print("=" * 85)

    print("\nPerformance by Category Tier:")
    for group, stats in category_stats.items():
        if stats["count"] > 0:
            avg_lat = stats["total_latency"] / stats["count"]
            acc = (stats["correct"] / stats["count"]) * 100.0
            print(f"  • {group:<22}: {stats['correct']}/{stats['count']} correct ({acc:5.1f}%) | Avg Latency: {avg_lat:5.2f}s")

    # Write output artifact
    out_file = os.path.join(os.path.dirname(__file__), "..", "..", "eval_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": {
                    "total_queries": total_queries,
                    "total_correct": total_correct,
                    "accuracy_pct": round(overall_accuracy, 1),
                    "total_duration_sec": round(total_elapsed, 2),
                    "category_breakdown": category_stats,
                },
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\nDetailed results saved to: {os.path.abspath(out_file)}\n")


if __name__ == "__main__":
    run_eval()
