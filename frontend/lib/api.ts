/**
 * API client and TypeScript interfaces for IP-SAKTI Sahayak.
 */

export type FormulationCategory =
  | "classical_generic"
  | "patent_or_proprietary"
  | "new_non_classical_drug"
  | "phytopharmaceutical"
  | "ayurveda_aahar_nutraceutical"
  | "cosmetic"
  | "unknown";

export interface DecisionOption {
  id: string;
  label: string;
  description?: string;
}

export interface DecisionQuestion {
  id: string;
  text: string;
  subtext?: string;
  rationale?: string;
  options: DecisionOption[];
  step_number?: number;
  total_steps?: number;
}

export interface CategoryOutcome {
  category_id: FormulationCategory;
  name: string;
  description: string;
  key_implications: string[];
  tkdl_status?: string;
  abs_requirement?: string;
  clinical_requirement?: string;
}

export interface ClassificationStartResponse {
  session_id: string;
  question: DecisionQuestion;
  completed: boolean;
  category: CategoryOutcome | null;
}

export interface ClassificationNextResponse {
  session_id: string;
  question: DecisionQuestion | null;
  completed: boolean;
  category: CategoryOutcome | null;
}

export interface CitationItem {
  chunk_id: string;
  instrument_name: string;
  section_number: string | null;
  parent_section_label: string | null;
  authority_level: string;
  source_url: string;
  text_snippet: string;
  rank_position: number;
  retrieval_score?: number;
}

export interface QueryRequest {
  query_text: string;
  jurisdiction: "india" | "international";
  formulation_category: FormulationCategory;
  language: "en" | "hi";
  top_k?: number;
  session_id?: string;
  user_id?: string;
}

export interface QueryResponse {
  query_id: string;
  query_text: string;
  jurisdiction: string;
  formulation_category: string;
  language: string;
  answer: string | null;
  citations: CitationItem[];
  confidence_score: number;
  abstained: boolean;
  abstention_reason: string | null;
  escalation_offered: boolean;
  generation_attempts: number;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export const api = {
  async checkHealth(): Promise<{ status: string; ollama_model?: string }> {
    try {
      const res = await fetch(`${BACKEND_URL}/health`, { method: "GET" });
      if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Backend health check failed:", err);
      return { status: "offline" };
    }
  },

  async startClassification(language: "en" | "hi" = "en"): Promise<ClassificationStartResponse> {
    const sessionId = `sess_${Date.now()}`;
    const res = await fetch(`${BACKEND_URL}/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: language,
        session_id: sessionId,
      }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to start classification (${res.status})`);
    }
    const data = await res.json();
    const isCompleted = data.status === "completed";
    return {
      session_id: data.session_id || sessionId,
      completed: isCompleted,
      question: data.current_question ? {
        id: data.current_question.node_id,
        text: data.current_question.question,
        subtext: data.current_question.description,
        options: data.current_question.options.map((opt: any) => ({
          id: opt.id,
          label: opt.label,
        })),
      } : (null as any),
      category: isCompleted && data.outcome ? {
        category_id: data.outcome.category_code,
        name: data.outcome.display_name,
        description: data.outcome.notes,
        key_implications: [
          data.outcome.ip_posture_summary,
          data.outcome.abs_guidance,
        ].filter(Boolean),
      } : null,
    };
  },

  async nextClassificationStep(
    sessionId: string,
    currentQuestionId: string,
    selectedOptionId: string,
    language: "en" | "hi" = "en"
  ): Promise<ClassificationNextResponse> {
    const res = await fetch(`${BACKEND_URL}/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        language: language,
        current_node_id: currentQuestionId,
        selected_option_id: selectedOptionId,
      }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to advance classification (${res.status})`);
    }
    const data = await res.json();
    const isCompleted = data.status === "completed";
    return {
      session_id: data.session_id || sessionId,
      completed: isCompleted,
      question: data.current_question ? {
        id: data.current_question.node_id,
        text: data.current_question.question,
        subtext: data.current_question.description,
        options: data.current_question.options.map((opt: any) => ({
          id: opt.id,
          label: opt.label,
        })),
      } : null,
      category: isCompleted && data.outcome ? {
        category_id: data.outcome.category_code,
        name: data.outcome.display_name,
        description: data.outcome.notes,
        key_implications: [
          data.outcome.ip_posture_summary,
          data.outcome.abs_guidance,
        ].filter(Boolean),
      } : null,
    };
  },

  async submitQuery(request: QueryRequest): Promise<QueryResponse> {
    const res = await fetch(`${BACKEND_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Query failed (${res.status})`);
    }
    return await res.json();
  },
};
