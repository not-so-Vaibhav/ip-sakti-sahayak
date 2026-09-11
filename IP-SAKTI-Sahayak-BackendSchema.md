# Backend Schema: IP-SAKTI Sahayak

**Companion to:** IP-SAKTI-Sahayak-PRD.md, IP-SAKTI-Sahayak-TRD.md
**Scope:** Full relational schema (Supabase/Postgres) + vector store schema (Qdrant)

This document is the concrete DDL-level extension of TRD Section 4 — it's
what someone actually runs to stand up the database, not a sketch of it.

---

## 1. Two Stores, One Join Key

- **Supabase (Postgres):** canonical metadata, user/session data, audit
  trail, and a text mirror of every chunk (for admin review and re-ingestion
  — the vectors themselves don't live here)
- **Qdrant:** the vectors + a payload copy of the filterable metadata fields
  (jurisdiction, regime_category, etc.) needed for fast retrieval-time
  filtering

They're joined by a single shared key: **`chunk_id` (uuid)**, generated once
at ingestion time and written to both stores. Postgres is the source of
truth for metadata; Qdrant is optimized for filtered vector search. If they
ever disagree, Postgres wins and Qdrant gets re-synced.

---

## 2. Enum Types (Postgres)

```sql
CREATE TYPE jurisdiction_type AS ENUM ('india', 'international');

CREATE TYPE regime_category_type AS ENUM (
  'patent', 'gi', 'trademark', 'copyright', 'design', 'plant_variety',
  'abs', 'drug_regulatory', 'food_regulatory', 'advertising'
);

CREATE TYPE authority_level_type AS ENUM (
  'primary_law', 'rule', 'treaty', 'classical_reference',
  'case_law', 'institutional_guidance'
);

CREATE TYPE formulation_category_type AS ENUM (
  'classical_generic', 'patent_or_proprietary', 'new_non_classical_drug',
  'phytopharmaceutical', 'ayurveda_aahar_nutraceutical', 'cosmetic'
);

CREATE TYPE language_type AS ENUM ('en', 'hi');
```

---

## 3. Core Tables

### 3.1 `users`

```sql
CREATE TABLE users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email         text UNIQUE,
  display_name  text,
  role          text NOT NULL DEFAULT 'general'
                  CHECK (role IN ('general', 'startup', 'researcher',
                                   'official', 'facilitator', 'admin')),
  created_at    timestamptz NOT NULL DEFAULT now()
);
```
`role` lets the frontend tailor language slightly (per PRD persona table)
without needing a separate profile system for the MVP.

### 3.2 `corpus_documents` (instrument-level)

```sql
CREATE TABLE corpus_documents (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_name    text NOT NULL,               -- e.g. "The Patents Act, 1970"
  jurisdiction        jurisdiction_type NOT NULL,
  regime_category     regime_category_type NOT NULL,
  authority_level      authority_level_type NOT NULL,
  source_url            text NOT NULL,
  effective_date         date,
  last_amended_date       date,
  current_version_id       uuid,                    -- FK set after corpus_versions insert
  created_at                timestamptz NOT NULL DEFAULT now(),
  UNIQUE (instrument_name, jurisdiction)
);
```

### 3.3 `corpus_versions` (version history per instrument)

```sql
CREATE TABLE corpus_versions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id       uuid NOT NULL REFERENCES corpus_documents(id) ON DELETE CASCADE,
  version_date       date NOT NULL,                -- date this version became effective
  ingested_at          timestamptz NOT NULL DEFAULT now(),
  source_url_snapshot   text NOT NULL,               -- URL as it was when ingested
  superseded_by          uuid REFERENCES corpus_versions(id),
  notes                   text
);

ALTER TABLE corpus_documents
  ADD CONSTRAINT fk_current_version
  FOREIGN KEY (current_version_id) REFERENCES corpus_versions(id);
```
This is what implements the PRD's "corpus currency / last verified timestamp"
requirement at the schema level — every chunk points to a specific version,
so an amendment doesn't silently overwrite history.

### 3.4 `corpus_chunks` (clause-level — mirrors Qdrant payload)

```sql
CREATE TABLE corpus_chunks (
  chunk_id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id                     uuid NOT NULL REFERENCES corpus_documents(id) ON DELETE CASCADE,
  version_id                        uuid NOT NULL REFERENCES corpus_versions(id),
  section_number                     text,           -- e.g. "3(p)"
  parent_section_label                 text,           -- e.g. "Chapter II — Inventions Not Patentable"
  text_content                          text NOT NULL,
  language                                language_type NOT NULL DEFAULT 'en',
  formulation_category_relevance           formulation_category_type[],  -- can apply to multiple
  embedding_model_version                    text NOT NULL,   -- e.g. "multilingual-e5-large-v1"
  qdrant_point_synced                          boolean NOT NULL DEFAULT false,
  created_at                                     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document ON corpus_chunks(document_id);
CREATE INDEX idx_chunks_formulation_relevance ON corpus_chunks USING GIN (formulation_category_relevance);
```

### 3.5 `classification_sessions`

```sql
CREATE TABLE classification_sessions (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid REFERENCES users(id),
  answers_json            jsonb NOT NULL,           -- raw Q&A trail through the decision tree
  resulting_category        formulation_category_type,
  tree_version_tag             text NOT NULL,          -- which decision-tree config version was used
  created_at                     timestamptz NOT NULL DEFAULT now()
);
```

### 3.6 `query_logs`

```sql
CREATE TABLE query_logs (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                    uuid REFERENCES users(id),
  classification_session_id    uuid REFERENCES classification_sessions(id),
  query_text                     text NOT NULL,
  language                          language_type NOT NULL,
  jurisdiction_selected               jurisdiction_type NOT NULL,
  confidence_score                      numeric(4,3),  -- 0.000–1.000
  abstained                               boolean NOT NULL DEFAULT false,
  escalated                                 boolean NOT NULL DEFAULT false,
  answer_text                                text,
  created_at                                   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_query_logs_user ON query_logs(user_id);
CREATE INDEX idx_query_logs_created ON query_logs(created_at);
```

### 3.7 `query_citations` (join table — one query can cite many chunks)

```sql
CREATE TABLE query_citations (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        uuid NOT NULL REFERENCES query_logs(id) ON DELETE CASCADE,
  chunk_id          uuid NOT NULL REFERENCES corpus_chunks(chunk_id),
  rank_position       integer NOT NULL,             -- 1 = most relevant citation shown
  retrieval_score        numeric(5,4)                 -- raw score from retrieval, pre-confidence-aggregation
);

CREATE INDEX idx_query_citations_query ON query_citations(query_id);
```
This normalizes the `retrieved_chunk_ids` array hinted at in the TRD into a
real join table — needed because the evaluation plan (PRD Section 9) checks
citation correctness per-citation, not per-query.

### 3.8 `escalations`

```sql
CREATE TABLE escalations (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id         uuid NOT NULL REFERENCES query_logs(id),
  user_id            uuid REFERENCES users(id),
  reason               text NOT NULL
                          CHECK (reason IN ('low_confidence', 'out_of_scope',
                                              'user_requested', 'no_source_found')),
  status                 text NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'assigned', 'resolved')),
  facilitator_notes         text,
  created_at                   timestamptz NOT NULL DEFAULT now(),
  resolved_at                    timestamptz
);
```

### 3.9 `permission_logs`

```sql
CREATE TABLE permission_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES users(id),
  connector_name      text NOT NULL,                -- e.g. "Manupatra", "SCC Online"
  scope                 text NOT NULL,                -- what access was granted
  granted_at              timestamptz NOT NULL DEFAULT now(),
  revoked_at                timestamptz
);
```
Every use of a user's own paid-source subscription (PRD FR7) must have a
row here **before** the connector is invoked — this table is the technical
enforcement of "explicit, logged permission," not just a UI checkbox.

### 3.10 `formulation_categories` (lookup / content table)

```sql
CREATE TABLE formulation_categories (
  code                          formulation_category_type PRIMARY KEY,
  display_name_en                 text NOT NULL,
  display_name_hi                    text NOT NULL,
  ip_posture_summary_en                 text NOT NULL,
  ip_posture_summary_hi                    text NOT NULL
);
```
This backs the classifier's result screen (UI/UX doc Section 5.2) — the
explanation text is data, not hardcoded frontend copy, so it can be updated
without a redeploy.

---

## 4. Entity Relationship Summary

```
users ──1:N── classification_sessions ──1:N── query_logs ──1:N── query_citations ──N:1── corpus_chunks
  │                                                  │                                        │
  └──1:N── permission_logs                           └──1:N── escalations                     └──N:1── corpus_versions ──N:1── corpus_documents
```

---

## 5. Qdrant Collection Schema

```json
{
  "collection_name": "ip_sakti_chunks",
  "vectors": {
    "size": 1024,
    "distance": "Cosine"
  },
  "sparse_vectors": {
    "bm25": {}
  }
}
```

**Payload schema** (mirrors the filterable fields from `corpus_chunks` —
kept intentionally slim; full text and admin metadata stay in Postgres):

```json
{
  "chunk_id": "uuid",            // matches Postgres corpus_chunks.chunk_id exactly
  "jurisdiction": "india",
  "regime_category": "patent",
  "formulation_category_relevance": ["classical_generic"],
  "language": "en",
  "authority_level": "primary_law",
  "instrument_name": "The Patents Act, 1970",
  "section_number": "3(p)"
}
```

**Required payload indexes** (Qdrant needs these explicitly for filter
performance — don't skip this, unindexed payload filters degrade badly at
even a few thousand points):

```python
client.create_payload_index(collection_name="ip_sakti_chunks", field_name="jurisdiction", field_schema="keyword")
client.create_payload_index(collection_name="ip_sakti_chunks", field_name="regime_category", field_schema="keyword")
client.create_payload_index(collection_name="ip_sakti_chunks", field_name="formulation_category_relevance", field_schema="keyword")
client.create_payload_index(collection_name="ip_sakti_chunks", field_name="language", field_schema="keyword")
```

---

## 6. Sync Discipline (Postgres ↔ Qdrant)

1. Ingest raw source → chunk → write full record to `corpus_chunks` in
   Postgres first (`qdrant_point_synced = false`)
2. Generate embedding → upsert to Qdrant using the **same `chunk_id`** as
   the point ID → on success, set `qdrant_point_synced = true` in Postgres
3. If a source document is amended: insert a new `corpus_versions` row,
   re-chunk, insert new `corpus_chunks` rows pointing to the new version —
   **do not overwrite old chunks**, so historical answers remain
   reconstructable (this is what the audit requirement in the PRD actually
   depends on)
4. Old chunks from a superseded version are excluded from retrieval via a
   `WHERE version_id = current_version_id` join at query time — kept in
   Postgres, removed from Qdrant's active filter set (either deleted from
   Qdrant or tagged with `is_current: false` in payload and filtered out)

---

## 7. Migration & Seed Notes for the Hackathon

- Seed `formulation_categories` (Section 3.10) first — the classifier result
  screen and several other flows depend on it existing
- Run corpus ingestion (Section 6, step 1–2) as an offline batch script
  against the documents collected per the team's data-collection assignments
  — not a live pipeline for the MVP
- Keep a small `eval/` seed set of hand-verified `query_logs` +
  `query_citations` rows to sanity-check that the schema actually supports
  the accuracy/citation-correctness testing described in the TRD's
  evaluation plan, before building the full ingestion pipeline
