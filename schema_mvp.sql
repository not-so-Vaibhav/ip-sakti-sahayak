-- IP-SAKTI Sahayak — Trimmed MVP Schema
-- Run this directly against Supabase (SQL editor or migration).
-- This is the MVP-scoped subset of the full Backend Schema doc —
-- version history, permission_logs, and escalation workflow are
-- deliberately omitted; see MVP-Build-Scope.md for what's cut and why.

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

-- Users (minimal — no auth complexity for MVP)
CREATE TABLE users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name  text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- Instrument-level document metadata (no version history table for MVP —
-- re-ingesting just overwrites the row's last_amended_date/source_url)
CREATE TABLE corpus_documents (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_name    text NOT NULL,
  jurisdiction       jurisdiction_type NOT NULL,
  regime_category    regime_category_type NOT NULL,
  authority_level    authority_level_type NOT NULL,
  source_url         text NOT NULL,
  effective_date     date,
  last_amended_date  date,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (instrument_name, jurisdiction)
);

-- Clause-level chunks — mirrors what's embedded in Qdrant, joined by chunk_id
CREATE TABLE corpus_chunks (
  chunk_id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id                     uuid NOT NULL REFERENCES corpus_documents(id) ON DELETE CASCADE,
  section_number                  text,
  parent_section_label            text,
  text_content                    text NOT NULL,
  language                        language_type NOT NULL DEFAULT 'en',
  formulation_category_relevance  formulation_category_type[],
  embedding_model_version         text NOT NULL,
  qdrant_point_synced             boolean NOT NULL DEFAULT false,
  created_at                      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document ON corpus_chunks(document_id);
CREATE INDEX idx_chunks_formulation_relevance ON corpus_chunks USING GIN (formulation_category_relevance);

-- Classifier session results
CREATE TABLE classification_sessions (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid REFERENCES users(id),
  answers_json        jsonb NOT NULL,
  resulting_category  formulation_category_type,
  tree_version_tag    text NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now()
);

-- Every query + its outcome
CREATE TABLE query_logs (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                     uuid REFERENCES users(id),
  classification_session_id  uuid REFERENCES classification_sessions(id),
  query_text                 text NOT NULL,
  language                   language_type NOT NULL,
  jurisdiction_selected      jurisdiction_type NOT NULL,
  confidence_score           numeric(4,3),
  abstained                  boolean NOT NULL DEFAULT false,
  escalated                  boolean NOT NULL DEFAULT false,  -- simple flag, no workflow table
  answer_text                text,
  created_at                 timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_query_logs_user ON query_logs(user_id);

-- Citations per query — needed to grade citation-correctness per source, not just per answer
CREATE TABLE query_citations (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id         uuid NOT NULL REFERENCES query_logs(id) ON DELETE CASCADE,
  chunk_id         uuid NOT NULL REFERENCES corpus_chunks(chunk_id),
  rank_position    integer NOT NULL,
  retrieval_score  numeric(5,4)
);

CREATE INDEX idx_query_citations_query ON query_citations(query_id);

-- Classifier result content (bilingual, editable without redeploy)
CREATE TABLE formulation_categories (
  code                     formulation_category_type PRIMARY KEY,
  display_name_en          text NOT NULL,
  display_name_hi          text NOT NULL,
  ip_posture_summary_en    text NOT NULL,
  ip_posture_summary_hi    text NOT NULL
);
