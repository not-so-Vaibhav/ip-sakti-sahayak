# IP-SAKTI Sahayak — MVP Build Scope (Hackathon)

This document defines what actually gets built, trimmed from the full PRD/TRD.
If something isn't listed here, don't build it yet — check with the team first.

## Build, in this order

1. **Formulation classifier** (`/classify`) — deterministic decision tree,
   config-driven (JSON/YAML), NOT hardcoded if/else, NOT an LLM call.
   The example tree in the TRD is a placeholder — implement it as-is for now
   so the pipeline works end to end, but keep it in an easily editable
   config file since the actual questions will likely be corrected later.
2. **Ingestion pipeline** — chunk documents by legal section/article
   (not fixed token windows), embed with a multilingual embedding model,
   write to Qdrant + a Postgres metadata mirror.
3. **Hybrid retrieval** — dense (embedding similarity) + sparse (BM25/keyword)
   combined, filtered by jurisdiction + formulation_category metadata
   BEFORE ranking, not after.
4. **Confidence scoring + abstention** — start with a simple formula
   (normalize top retrieval score, reduce if fewer than 2 corroborating
   chunks). Treat the 0.5 threshold as a placeholder to be tuned once real
   test data exists — make it a config value, not a hardcoded constant.
5. **Citation-constrained generation** (`/query`) — model may only assert
   claims traceable to retrieved chunks. After generation, validate that
   every citation marker in the output maps to an actually-retrieved
   chunk ID (simple ID matching) — reject/regenerate if not.
6. **Frontend** — chat interface, jurisdiction toggle, language switch
   (English/Hindi), citation list with source-viewer panel, confidence
   indicator, distinct abstention state.
7. **Eval set** — 15–20 hand-written Q&A pairs with known-correct answers,
   used to sanity check accuracy/citation-correctness/abstention behavior.

## Explicitly OUT of scope for the hackathon build

- ABS-compliance helper as a separate module (fold its explanation into the
  classifier's result text instead)
- `permission_logs` / paid-source connectors
- Corpus version history (overwrite chunks on re-ingest; no version table)
- `escalations` workflow (a boolean `escalated` flag on the query is enough)
- Knowledge graph / agentic multi-step orchestration
- Voice interface
- Any language beyond English + Hindi
- Fine-tuning the LLM (use a well-prompted base model; only revisit if there's
  time left after everything above works)

## Tech stack (locked in)

- Backend: Python, FastAPI
- Vector DB: Qdrant (Docker, local)
- Relational DB: Supabase (Postgres) — trimmed schema, see `schema_mvp.sql`
- Embeddings: self-hosted multilingual model (multilingual-e5-large or
  similar) — no external embedding API
- Generation LLM: self-hosted open-weight model via Ollama (local dev,
  small model e.g. Qwen3 4B) and a cloud GPU (Colab/Kaggle) for the
  full-size model (Qwen3 8B/14B or Llama 3.1 8B) used in the real
  pipeline/demo — no OpenAI/Anthropic/Google API calls anywhere
- Frontend: Next.js + Tailwind CSS

## Definition of done for the hackathon demo

A user can: pick a language → run the classifier → get a category → ask a
question in either jurisdiction → get an answer with real, clickable
citations and a visible confidence indicator → see a genuinely different
screen state when the system abstains → and there's a hand-checked eval set
proving this actually works on 15–20 known questions, not just the one
you'll demo live.
