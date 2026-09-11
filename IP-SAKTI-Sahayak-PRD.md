# Product Requirements Document: IP-SAKTI Sahayak

**Problem Statement ID:** SIH26045 | **Ministry:** AYUSH | **Category:** Software
**Version:** 1.0 (Hackathon submission draft)

---

## 1. Overview

IP-SAKTI Sahayak is a multilingual, retrieval-augmented (RAG) AI assistant that
answers Intellectual Property and regulatory questions specific to Ayurveda,
across both Indian and international legal regimes. Every answer is grounded in
a version-tracked corpus of primary legal sources and is traceable to a specific
statute, rule, treaty article, or record — the assistant explicitly does not
generate legal claims it cannot cite.

The product exists because IP protection for an Ayurvedic product cannot be
separated from how that product is regulated. A single formulation might need
to be evaluated simultaneously against patent law, GI/trademark law, Access-
and-Benefit-Sharing (ABS) duties under India's biodiversity law, and drug/food/
cosmetic regulatory classification — and today, no single tool helps a
practitioner, researcher, or AYUSH startup navigate all of that together.

---

## 2. Problem Statement (from the official brief)

Ayurveda rests on a vast corpus of codified and community-held traditional
knowledge (TK), and on therapeutics derived from plant, microbial, and animal
sources. Commercializing an Ayurvedic product means navigating overlapping
regimes at once: patents, GI, trademarks, copyright, designs, trade secrets,
and plant-variety rights; ABS duties flowing from India's sovereignty over its
biological resources; and the drug-regulatory framework that decides whether a
formulation is a classical medicine, a proprietary medicine, a new drug, a
phytopharmaceutical, a food, or a cosmetic.

Practitioners, researchers, AYUSH startups/MSMEs, and cultivators routinely
struggle with this. The result is twofold: legitimate Ayurvedic innovation is
under-protected and under-commercialized, while India's traditional knowledge
remains exposed to misappropriation abroad. Recent developments — the 2024
Patent and Biodiversity Rules and the 2024 WIPO Treaty on Genetic Resources and
Associated Traditional Knowledge — make authoritative, plain-language guidance
more necessary than ever. No such tool currently exists for the AYUSH community.

---

## 3. Goals

- **G1.** Let a user get an accurate, source-cited answer to an Ayurveda-specific
  IP/regulatory question in plain language, in English or Hindi.
- **G2.** Classify a formulation into its correct regulatory category before
  answering, since IP posture depends entirely on that classification.
- **G3.** Keep Indian and international law visibly separate via an explicit
  jurisdiction toggle — answers from the two are never conflated.
- **G4.** Surface ABS obligations and TKDL/prior-art considerations proactively,
  not only when explicitly asked.
- **G5.** Never present an unsourced claim as fact — abstain and escalate to a
  human IP facilitator when confidence is low or the query is out of scope.
- **G6.** Be usable by someone who is not a lawyer and may not be fluent in
  English legal terminology.

### Non-Goals (explicitly out of scope)

- **Not a medical/efficacy advisor.** The assistant does not adjudicate whether
  a remedy "works," verify folk-medicine claims, or answer general-public
  health questions (e.g. "is eating neem good for X"). This is an IP and
  regulatory tool for practitioners/innovators, not a health-myth checker.
- **Not a substitute for a lawyer.** Every response carries an "information,
  not legal advice" disclaimer; complex or high-confidence-required cases
  route to a human IP facilitator.
- **Not ingesting TKDL's actual database.** TKDL's searchable records are
  confidential and restricted to patent-office examiners under bilateral
  agreements. The assistant may reference TKDL's existence, its
  classification system, and its public case outcomes only.
- **Not covering every export market.** International herbal-market coverage
  is scoped to a small, named set of jurisdictions (e.g. US, EU) rather than
  attempting exhaustive global coverage.

---

## 4. Target Users

| Persona | Need |
|---|---|
| Ayurveda startup / MSME founder | "Can I patent or protect this formulation? What license do I need to sell it?" |
| Individual practitioner / Vaidya | "Is my classical remedy safe from being wrongly patented elsewhere?" |
| Academic researcher | "What's the IP status of this plant-derived compound, and what ABS duties apply if I publish or license it?" |
| AYUSH ministry official / examiner | "Quick, cited lookup across statutes and treaties instead of manual cross-referencing." |
| Cultivator / biological-resource holder | "What are my rights and obligations if a company wants to use knowledge from my community?" |

---

## 5. Functional Requirements

### FR1 — Formulation Classification (entry flow)
Before answering an IP question, the assistant runs a **deterministic decision
tree** (not LLM-guessed) to classify the product into one of:
classical/generic medicine · patent-or-proprietary medicine · new/non-classical
drug · phytopharmaceutical · Ayurveda-Aahar/nutraceutical · cosmetic.

- Asks the minimum number of clarifying questions needed to classify
- Each category maps to a distinct explanation of its IP and ABS posture
  (e.g., a classical formulation is largely TK, faces the Patents Act
  **Section 3(p)** bar, and is defended via TKDL prior art; a new drug has
  genuine patent potential but requires clinical safety/efficacy evidence)
- Classification result becomes a **metadata filter** for all downstream
  retrieval — this is the hand-off point between the deterministic classifier
  and the RAG engine

### FR2 — Jurisdiction Toggle
- Explicit National vs. International switch, user-controlled
- Retrieval is filtered by jurisdiction tag at the query level — not just a
  UI label — so the two answer-sets are never blended in one response
- National: Patents Act, GI Act, Trade Marks Act, Designs Act, Copyright Act,
  Plant Variety Protection Act, Biological Diversity Act, Drugs & Cosmetics
  Act, Drugs and Magic Remedies Act, FSSAI Ayurveda Aahara Regulations
- International: TRIPS, CBD + Nagoya Protocol, WIPO GRATK Treaty (2024), PCT,
  Madrid Protocol, Hague System, Budapest Treaty, select export-market rules

### FR3 — Grounded Q&A with Mandatory Citation
- Every answer must be traceable to a specific statute/rule/treaty
  article/record; the model is constrained to only assert what's supported
  by retrieved source chunks
- Inline citation markers → reference list → each one links to the source
  clause in a viewer pane
- **Confidence indicator** attached to every answer, derived from
  retrieval/rerank scores and corroborating-source count
- **Safe abstention:** below a confidence threshold, or for out-of-scope
  queries, the assistant declines to answer and offers escalation instead
  of guessing

### FR4 — ABS-Compliance Helper
- Surfaces Access-and-Benefit-Sharing obligations under the Biological
  Diversity Act/Rules when a query touches use of biological resources or
  associated TK
- Points the user to the correct NBA registration/approval form category

### FR5 — TKDL / Prior-Art Pointer
- References TKDL's role and public classification system where relevant
- Surfaces documented precedent cases (e.g. Turmeric, Neem) as illustrative
  context
- Does **not** claim to search TKDL's confidential database

### FR6 — Escalation to Human IP Facilitator
- Defined handoff path when confidence is low, the query is legally complex,
  or the user explicitly requests human review

### FR7 — Source Access Facilitation
- Helps the user navigate from a question to the correct official registry,
  record, or form (e.g. IP India public search, NBA forms)
- May use the user's own paid legal-database subscription **only with
  explicit, logged permission** — never by default

### FR8 — Multilingual Delivery
- English and Hindi at MVP stage, built on national language infrastructure
  (Bhashini) rather than a generic translation bolt-on
- Cross-lingual retrieval: a Hindi query must retrieve the same source
  clause as the equivalent English query

### FR9 — Standing Disclaimers & Guardrails
- Persistent "information, not legal advice" disclaimer on every session
- No fabricated authority under any circumstance — this is a hard constraint,
  not a style preference

---

## 6. Non-Functional Requirements

- **Corpus currency:** version-tracked source documents with "last verified"
  timestamps; a defined process for re-ingesting amended law
- **Privacy & security:** aligned with the Digital Personal Data Protection
  (DPDP) Act; audit logging for any use of paid-source connectors
- **Auditability:** every answer's retrieval trail (which chunks, which
  confidence score) should be reconstructable for review
- **Latency:** answers should return within a few seconds for a demo-quality
  experience; retrieval and generation should not require the classification
  step to re-run unnecessarily
- **Evaluability:** the system must be measurable on the criteria named in
  the brief — answer accuracy, citation correctness, safe abstention rate on
  out-of-scope/uncertain queries, and multilingual quality

---

## 7. System Architecture (high level)

```
User Query
   │
   ▼
Language Detection ──► (routes English/Hindi through same pipeline)
   │
   ▼
Formulation Classifier (deterministic decision tree)
   │  → outputs: category + regulatory metadata filter
   ▼
Jurisdiction Filter (National / International, user-selected)
   │
   ▼
Hybrid Retrieval (dense + sparse/BM25) over versioned, chunked legal corpus
   │  → metadata-filtered by: jurisdiction, regime_category, formulation_category
   ▼
Grounded Generation (constrained to retrieved chunks only)
   │  → confidence scoring against retrieval/rerank strength
   ▼
   ├── High confidence → Answer + inline citations + source viewer links
   └── Low confidence / out-of-scope → Abstain + escalate to human IP facilitator
```

**Core components:**
- **Retrieval layer:** vector DB with strong metadata filtering + hybrid
  search (dense embeddings + keyword/BM25) — needed because legal queries
  require exact-term matching (e.g. "Section 3(p)") alongside semantic search
- **Embeddings:** multilingual by design (e.g. multilingual-e5-large or
  LaBSE) so English source text and Hindi queries land in the same space
- **Classification engine:** rule-based, not LLM-guessed — reliability matters
  more than flexibility here, since this decision routes the entire downstream
  regulatory pathway
- **Generation layer:** LLM constrained via retrieval-grounded prompting;
  no free-generation of legal claims
- **Orchestration:** agentic hand-off between classifier → jurisdiction filter
  → retrieval → generation, with the ABS helper and TKDL pointer as callable
  sub-modules rather than always-on steps

---

## 8. Data Requirements (summary — see team data-collection brief for full detail)

Chunking follows legal structure (section/article/rule), not fixed token
windows, since a citation must resolve to a specific clause. Each chunk
carries metadata: `instrument_name, section/article/rule_number, jurisdiction,
regime_category, formulation_category_relevance, effective_date,
last_amended_date, source_url, authority_level`.

Source categories: national statutes/rules, international treaties, the
Ayurvedic Pharmacopoeia and classical texts (for formulation classification
evidence only, not statutory authority), and AYUSH gazette notifications.
TKDL is referenced as an institution, not ingested as a database.

---

## 9. Success Metrics

| Metric | What it measures |
|---|---|
| Answer accuracy | Correctness of substantive IP/regulatory guidance against known-correct answers |
| Citation correctness | Whether the cited clause actually supports the claim made |
| Safe abstention rate | Whether the system correctly declines on out-of-scope or low-confidence queries instead of guessing |
| Multilingual quality | Parity of answer quality and citation accuracy between English and Hindi queries |
| Classification accuracy | Whether the formulation decision tree correctly routes to the right category |

These map directly to the evaluation criteria named in the official brief —
the hackathon demo should be designed to visibly exercise each one at least
once.

---

## 10. Staged Roadmap

| Stage | Scope |
|---|---|
| **Stage 1 — Hackathon MVP** | Citation-grounded retrieval over a curated national + international corpus; formulation classifier (rule-based); jurisdiction toggle; confidence indicator + abstention; English + Hindi |
| **Stage 2** | Knowledge graph over regulatory relationships; agentic multi-step orchestration (classifier → ABS helper → TKDL pointer as coordinated sub-agents) |
| **Stage 3** | Paid-source connectors (user's own subscriptions, with explicit logged permission) |
| **Stage 4** | Full multilingual expansion beyond Hindi + voice interface |

The hackathon deliverable is Stage 1 only — the deck and demo should frame
Stages 2–4 explicitly as roadmap, not claim them as built.

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated legal claim | Citation-constrained generation; hard abstention below confidence threshold |
| Corpus goes stale as law amends | Versioned ingestion with "last verified" timestamps; defined re-ingestion process |
| Multilingual retrieval misses relevant clauses | Cross-lingual embeddings validated specifically on English↔Hindi legal-term pairs, not just general text |
| Team over-scopes international coverage | Cap at 2–3 export markets for MVP; expand only in later stages |
| Formulation classifier misroutes a query | Keep classification deterministic/rule-based rather than LLM-inferred, so errors are traceable and fixable |
| TKDL misrepresented as searchable | Explicit product copy and demo framing: TKDL is referenced, never queried directly |

---

## 12. Open Questions

- Which human-facilitator escalation channel is realistic to demo (a mock
  handoff form, or an actual contact/API)?
- What's the MVP's exact confidence threshold for abstention, and how will
  it be tuned/validated before the demo?
- Should the knowledge-graph stage (Stage 2) be prototyped even partially for
  the hackathon, or purely described as roadmap?
