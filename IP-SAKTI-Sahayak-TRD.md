# Technical Requirements Document: IP-SAKTI Sahayak

**Problem Statement ID:** SIH26045 | Companion to: IP-SAKTI-Sahayak-PRD.md
**Scope:** Stage 1 (Hackathon MVP) implementation detail, with Stage 2–4 hooks noted

---

## 1. Purpose

This document specifies *how* IP-SAKTI Sahayak is built — components, data
schemas, APIs, models, and infrastructure — implementing the requirements in
the PRD. Where the PRD says *what* the system must do, this document says
*with what, exactly*.

---

## 2. System Architecture

```
┌─────────────┐
│  Frontend    │  Next.js + Tailwind — chat UI, jurisdiction toggle,
│  (Next.js)   │  source-viewer pane, language switch
└──────┬───────┘
       │ REST/JSON
┌──────▼───────────────────────────────────────────────────────────┐
│  API Layer (FastAPI)                                              │
│  ┌────────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │ /classify       │  │ /query             │  │ /escalate         │ │
│  │ (formulation     │  │ (main RAG          │  │ (human facilitator│ │
│  │  decision tree)  │  │  pipeline)         │  │  handoff)         │ │
│  └────────────────┘  └───────────────────┘  └──────────────────┘ │
└──────┬────────────────────┬───────────────────────┬──────────────┘
       │                    │                        │
┌──────▼──────┐   ┌─────────▼─────────┐    ┌────────▼────────┐
│ Classifier   │   │ Retrieval Engine   │    │ Supabase          │
│ Engine       │   │ (Qdrant + hybrid   │    │ (metadata, users,  │
│ (rule-based, │   │  search + rerank)  │    │  audit logs,       │
│  JSON tree)  │   │                    │    │  permission logs)  │
└──────────────┘   └─────────┬─────────┘    └────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Generation Layer   │
                    │ (LLM, citation-    │
                    │  constrained       │
                    │  prompting +       │
                    │  confidence score) │
                    └────────────────────┘
```

---

## 3. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend / orchestration | FastAPI + LangChain (or LlamaIndex) | Fast to build, good RAG-pipeline primitives |
| Vector DB | **Qdrant** (self-hosted, Docker) | Native payload/metadata filtering + hybrid (dense+sparse) search; open source, no managed-service cost for a hackathon |
| Embeddings | **multilingual-e5-large** (primary) or **LaBSE** (fallback) | Cross-lingual retrieval — English source law, Hindi query, same vector space |
| Sparse/keyword index | BM25 (via Qdrant's built-in sparse vectors or Elasticsearch if time allows) | Legal queries need exact-term match (e.g. "Section 3(p)"), not just semantic similarity |
| LLM (generation) | Any capable instruction-tuned model reachable via API; constrained via prompt + retrieval grounding | Swappable — the citation constraint is enforced at the prompt/pipeline level, not model-specific |
| Metadata / relational store | **Supabase** (Postgres) | Structured metadata, user sessions, audit + permission logs, classification results |
| Frontend | **Next.js + Tailwind CSS** | Fast to build a clean chat UI + source-viewer pane |
| Multilingual layer | **Bhashini** integration for Hindi (translation/ASR/TTS as needed) | Named explicitly in the brief as national language infrastructure — don't substitute a generic translation API for the MVP demo if avoidable |
| OCR (for scanned gazette notifications) | Tesseract | Some AYUSH circulars only exist as scanned PDFs |
| Auth (if needed for paid-source connectors) | Supabase Auth | Ties permission logging to a real user identity |

---

## 4. Data Model & Schemas

### 4.1 Document chunk schema (stored in Qdrant payload)

```json
{
  "chunk_id": "uuid",
  "text": "full text of this clause/section",
  "instrument_name": "The Patents Act, 1970",
  "section_number": "3(p)",
  "parent_section": "Chapter II — Inventions Not Patentable",
  "jurisdiction": "India",
  "regime_category": "patent",
  "formulation_category_relevance": ["classical_generic"],
  "authority_level": "primary_law",
  "effective_date": "1970-04-20",
  "last_amended_date": "2024-08-01",
  "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOAct/...",
  "language": "en",
  "embedding_model_version": "multilingual-e5-large-v1"
}
```

`regime_category` enum: `patent | GI | trademark | copyright | design |
plant_variety | ABS | drug_regulatory | food_regulatory | advertising`

`authority_level` enum: `primary_law | rule | treaty | classical_reference |
case_law | institutional_guidance`

### 4.2 Formulation classifier — decision tree representation

Represented as a JSON/YAML directed graph, **not** an LLM prompt — this must
be deterministic and auditable.

```yaml
start: q1_intended_use
nodes:
  q1_intended_use:
    question: "Is this formulation drawn directly from a First-Schedule authoritative classical text, unmodified?"
    options:
      yes: q_classify_classical
      no: q2_new_evidence
  q_classify_classical:
    outcome: "classical_generic"
    notes: "Faces Patents Act Sec. 3(p) bar; defended via TKDL prior art."
  q2_new_evidence:
    question: "Does the formulation include new combinations, processes, or dosage forms not in the classical text?"
    options:
      yes: q3_clinical_evidence
      no: q_classify_proprietary
  q_classify_proprietary:
    outcome: "patent_or_proprietary_medicine"
  q3_clinical_evidence:
    question: "Is there safety/efficacy evidence generated for this specific formulation?"
    options:
      yes: q_classify_new_drug
      no: q4_intended_category
  q_classify_new_drug:
    outcome: "new_non_classical_drug"
  q4_intended_category:
    question: "Is this intended as a food/dietary product, a phytopharmaceutical, or a cosmetic?"
    options:
      food: q_classify_aahar
      phytopharma: q_classify_phytopharma
      cosmetic: q_classify_cosmetic
  q_classify_aahar: { outcome: "ayurveda_aahar_nutraceutical" }
  q_classify_phytopharma: { outcome: "phytopharmaceutical" }
  q_classify_cosmetic: { outcome: "cosmetic" }
```

Each `outcome` maps to a `formulation_category_relevance` tag used to filter
retrieval, and to a canned explanation block (drafted from the PRD's FR1
description) describing that category's IP/ABS posture.

**Implementation note:** keep this as a standalone, testable module (e.g. a
pure function `classify(answers: dict) -> Category`) so it can be unit tested
independently of the LLM pipeline. This is the single most important
reliability boundary in the system — a classification error propagates into
every downstream retrieval filter.

### 4.3 Supabase tables (relational metadata)

```sql
-- classification_sessions
id, user_id, answers_json, resulting_category, created_at

-- query_logs
id, user_id, session_id, query_text, language, jurisdiction_selected,
retrieved_chunk_ids, confidence_score, answered (bool), escalated (bool),
created_at

-- permission_logs
id, user_id, connector_name, granted_at, revoked_at, scope

-- corpus_versions
id, instrument_name, version_date, source_url, ingested_at, superseded_by
```

---

## 5. API Design (MVP endpoints)

| Endpoint | Method | Purpose |
|---|---|---|
| `/classify` | POST | Runs the formulation decision tree; returns next question or final category |
| `/query` | POST | Main RAG pipeline: takes query + jurisdiction + category filter → returns answer, citations, confidence score |
| `/escalate` | POST | Logs an escalation request and returns handoff instructions/contact path |
| `/corpus/status` | GET | Returns corpus version/last-updated info per instrument — supports the "keep corpus current" requirement |
| `/permissions/grant` | POST | Logs explicit user consent before a paid-source connector is used |

`/query` request/response shape:

```json
// Request
{
  "query_text": "Can I patent a turmeric-based wound-healing paste?",
  "language": "en",
  "jurisdiction": "India",
  "formulation_category": "classical_generic"
}

// Response
{
  "answer": "...",
  "citations": [
    {"instrument": "The Patents Act, 1970", "section": "3(p)", "url": "..."}
  ],
  "confidence_score": 0.83,
  "abstained": false,
  "escalation_offered": false
}
```

---

## 6. Retrieval & Ranking

1. **Query preprocessing:** language detection → if Hindi, route through
   Bhashini for query normalization/translation-aware embedding lookup
   (embeddings are multilingual, so this is a light-touch step, not a full
   translate-then-search pipeline)
2. **Metadata pre-filter:** jurisdiction + formulation_category_relevance
   applied as a hard filter before vector search (Qdrant payload filter)
3. **Hybrid retrieval:** dense (embedding similarity) + sparse (BM25/keyword)
   combined — recommend reciprocal rank fusion or a simple weighted sum
   (start with weighted sum for MVP: `score = 0.6*dense + 0.4*sparse`, tune
   from there)
4. **Reranking (optional for MVP, recommended for Stage 2):** a cross-encoder
   rerank of the top-k candidates before generation
5. **Confidence score:** `confidence = f(top_chunk_score, num_corroborating_chunks_above_threshold)`
   — start simple: normalize top-1 retrieval score to [0,1], reduce it if
   fewer than 2 chunks agree
6. **Abstention rule:** if `confidence < 0.5` (tune during testing) OR
   retrieval returns zero chunks after metadata filtering → return
   `abstained: true` with an explanation and escalation offer, **never**
   fall back to ungrounded generation

---

## 7. Generation & Citation Enforcement

- System prompt constrains the model to only use provided retrieved chunks;
  explicitly instruct it to decline rather than fill gaps from its own
  knowledge
- Post-generation validation step: check that every citation marker in the
  output maps to an actually-retrieved chunk ID (reject/regenerate if not —
  simple string/ID matching, not another LLM call)
- Citation list rendered with clickable links into the source-viewer pane
  (highlighted clause, matching the UI shown in the pitch deck)

---

## 8. Multilingual Implementation

- **MVP scope: English + Hindi only** (per PRD non-goals — don't expand
  further for the hackathon)
- Query language detected client- or server-side; Bhashini used for any
  translation/normalization needs, not a generic third-party translate API,
  since the brief names Bhashini specifically
- Embedding model must be validated on English↔Hindi legal-term pairs before
  the demo — test with a small hand-built set of paired queries (e.g. "GI
  tag" / "भौगोलिक संकेत") to confirm both retrieve the same source chunk

---

## 9. Security & Compliance

- **DPDP alignment:** minimal PII collection; user query logs stored with
  a defined retention policy; no query content shared with third parties
  without consent
- **Permission logging:** any use of a user's own paid legal-database
  subscription requires an explicit, timestamped consent record
  (`permission_logs` table) before the connector is invoked
- **Audit trail:** every `/query` response's retrieval trail (chunk IDs,
  confidence score) is stored so an answer can be reconstructed and reviewed
- **No fabricated authority — enforced, not just stated:** the citation
  validation step in Section 7 is the technical enforcement of this
  requirement, not just a prompt instruction

---

## 10. Infrastructure & Deployment (MVP)

| Component | Hackathon deployment |
|---|---|
| Qdrant | Docker container, local or single cloud VM |
| FastAPI backend | Single container, same host as Qdrant for demo simplicity |
| Supabase | Managed free tier |
| Frontend | Vercel (Next.js default) or same VM |
| Corpus ingestion | Offline batch script (not a live pipeline for MVP) — run once against the collected source documents, re-run manually if sources are updated during the hackathon |

Stage 2+ (post-hackathon): move ingestion to a scheduled/triggered pipeline
that checks source URLs for updates and re-chunks/re-embeds automatically.

---

## 11. Testing & Evaluation Plan

Maps directly to PRD Section 9 metrics:

| Test | Method |
|---|---|
| Answer accuracy | Hand-built set of ~20–30 Q&A pairs with known-correct answers across categories; manual grading |
| Citation correctness | For each test answer, verify the cited clause actually supports the claim (manual review) |
| Safe abstention rate | Include deliberately out-of-scope or ambiguous queries in the test set; verify the system abstains rather than guesses |
| Multilingual parity | Run the same test set in Hindi; compare answer/citation quality to the English run |
| Classifier accuracy | Unit tests on the decision-tree module with known input→outcome pairs |

Build this test set **before** the demo, not after — it doubles as your
proof-of-quality slide material and as the actual QA process.

---

## 12. Non-Functional Targets (MVP)

- Query response time: target under 5 seconds end-to-end for the demo
- Corpus size: MVP targets ~20–30 primary instruments (per the team data
  collection brief) — not exhaustive coverage
- Availability: single-instance demo deployment is acceptable; no HA
  requirement at MVP stage

---

## 13. Suggested Repo Structure

```
ip-sakti-sahayak/
├── backend/
│   ├── api/            # FastAPI routes (/classify, /query, /escalate, ...)
│   ├── classifier/      # decision tree module + tests
│   ├── retrieval/        # Qdrant client, hybrid search, confidence scoring
│   ├── generation/       # prompt templates, citation validation
│   └── ingestion/        # offline corpus chunking + embedding scripts
├── frontend/            # Next.js app
├── data/
│   ├── raw_sources/      # collected PDFs/text (per team assignments doc)
│   └── processed_chunks/ # chunked + metadata-tagged output ready for ingestion
├── eval/                # test Q&A set, evaluation scripts
└── docs/                # PRD, TRD, pitch deck
```

---

## 14. Open Technical Risks

- Confidence-score threshold is untuned until real test-set results exist —
  don't hardcode 0.5 as final, treat it as a starting point
- Hybrid retrieval weighting (dense vs. sparse) needs empirical tuning once
  the real corpus is loaded — legal text may skew differently than general
  text
- Bhashini integration complexity is unknown until the team actually
  integrates it — have a fallback plan (a simpler translation step) ready
  if it can't be wired up in time, but disclose that substitution honestly
  in the demo rather than implying full Bhashini integration if it isn't there
