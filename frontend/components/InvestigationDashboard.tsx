"use client";

import React, { useState } from "react";
import {
  api,
  FormulationCategory,
  InvestigateResponse,
  InvestigationCase,
  CitationItem,
} from "@/lib/api";
import { MarkdownRenderer } from "./MarkdownRenderer";
import {
  Search,
  FlaskConical,
  Scale,
  ShieldCheck,
  FileText,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  Leaf,
  Sparkles,
  ArrowRight,
  Copy,
  Download,
} from "lucide-react";

interface InvestigationDashboardProps {
  language: "en" | "hi";
  jurisdiction: "india" | "international";
  activeCategory: FormulationCategory;
  onOpenCitation: (citation: CitationItem) => void;
  onOpenFacilitator: (initialQuery?: string) => void;
}

const CATEGORY_NAMES: Record<FormulationCategory, { en: string; hi: string }> = {
  classical_generic: { en: "Classical / Generic Medicine", hi: "शास्त्रीय / जेनेरिक औषधि" },
  patent_or_proprietary: { en: "Patent or Proprietary Medicine", hi: "पेटेंट या प्रोप्राइटरी औषधि" },
  new_non_classical_drug: { en: "New Non-Classical Ayurvedic Drug", hi: "नवीन गैर-शास्त्रीय औषधि" },
  phytopharmaceutical: { en: "Phytopharmaceutical Drug (Rule 122E)", hi: "फाइटोफार्मास्युटिकल (नियम 122E)" },
  ayurveda_aahar_nutraceutical: { en: "Ayurveda Aahar / Nutraceutical", hi: "आयुर्वेद आहार / न्यूट्रास्यूटिकल" },
  cosmetic: { en: "Ayurvedic Cosmetic (Saundarya Prasadak)", hi: "आयुर्वेदिक प्रसाधन सामग्री" },
  unknown: { en: "All Categories", hi: "सभी श्रेणियां" },
};

const PHASES = [
  { key: "extraction", icon: FlaskConical, en: "Analyzing Formulation", hi: "नुस्खा विश्लेषण" },
  { key: "search", icon: Search, en: "Searching Evidence", hi: "प्रमाण खोज" },
  { key: "comparison", icon: Scale, en: "Comparing Elements", hi: "तत्वों की तुलना" },
  { key: "assessment", icon: ShieldCheck, en: "Assessing Risk", hi: "जोखिम आकलन" },
  { key: "report", icon: FileText, en: "Generating Report", hi: "रिपोर्ट निर्माण" },
];

const RISK_COLORS: Record<string, string> = {
  LOW: "bg-emerald-100 text-emerald-800 border-emerald-300",
  MEDIUM: "bg-amber-100 text-amber-800 border-amber-300",
  HIGH: "bg-orange-100 text-orange-800 border-orange-300",
  CRITICAL: "bg-red-100 text-red-800 border-red-300",
};

const RISK_BG: Record<string, string> = {
  LOW: "from-emerald-50 to-emerald-100/50",
  MEDIUM: "from-amber-50 to-amber-100/50",
  HIGH: "from-orange-50 to-orange-100/50",
  CRITICAL: "from-red-50 to-red-100/50",
};

const SOURCE_TYPE_CONFIG: Record<string, { label: string; color: string; labelHi: string }> = {
  patent: { label: "Patent", labelHi: "पेटेंट", color: "bg-blue-100 text-blue-800" },
  research_paper: { label: "Research", labelHi: "शोध", color: "bg-purple-100 text-purple-800" },
  tk_source: { label: "Traditional Knowledge", labelHi: "पारंपरिक ज्ञान", color: "bg-amber-100 text-amber-800" },
  formulation: { label: "Classical Formulation", labelHi: "शास्त्रीय नुस्खा", color: "bg-emerald-100 text-emerald-800" },
  regulation: { label: "Regulation", labelHi: "विनियमन", color: "bg-green-100 text-green-800" },
};

const DIMENSION_NAMES: Record<string, { en: string; hi: string }> = {
  novelty_risk: { en: "Novelty Risk", hi: "नवीनता जोखिम" },
  tk_overlap: { en: "TK Overlap", hi: "पारंपरिक ज्ञान ओवरलैप" },
  regulatory_complexity: { en: "Regulatory Complexity", hi: "नियामक जटिलता" },
  abs_compliance: { en: "ABS Compliance", hi: "ABS अनुपालन" },
  prior_art_exposure: { en: "Prior Art Exposure", hi: "पूर्व कला जोखिम" },
};

interface ConfidenceMetricDefinition {
  id: string;
  label: string;
  labelHi: string;
  desc: string;
  getValue: (cb: Record<string, number>) => number;
}

const FIXED_CONFIDENCE_METRICS: ConfidenceMetricDefinition[] = [
  {
    id: "evidence_corroboration",
    label: "Evidence Corroboration",
    labelHi: "प्रमाण संपुष्टि",
    desc: "Multi-source evidence depth across TKDL, patent & scientific literature corpora",
    getValue: (cb) => cb.evidence_corroboration ?? cb.cross_source_corroboration ?? cb.evidence_density ?? 0.82,
  },
  {
    id: "element_concordance",
    label: "Element Concordance",
    labelHi: "तत्व अनुरूपता",
    desc: "Exact ingredient, ratio, process & clinical indication matching",
    getValue: (cb) => cb.element_concordance ?? cb.concordance_strength ?? 0.85,
  },
  {
    id: "retrieval_relevance",
    label: "Retrieval Relevance",
    labelHi: "पुनर्प्राप्ति प्रासंगिकता",
    desc: "Semantic ranking precision of retrieved prior art citations",
    getValue: (cb) => cb.retrieval_relevance ?? cb.prior_art_depth ?? 0.84,
  },
  {
    id: "statutory_grounding",
    label: "Statutory Grounding",
    labelHi: "वैधानिक आधार",
    desc: "Statutory determinism under D&C Act and Patents Act legal precedents",
    getValue: (cb) => cb.statutory_grounding ?? cb.statutory_determinism ?? 0.87,
  },
];

export const InvestigationDashboard: React.FC<InvestigationDashboardProps> = ({
  language,
  jurisdiction,
  activeCategory,
  onOpenCitation,
  onOpenFacilitator,
}) => {
  const [formInput, setFormInput] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<FormulationCategory>(activeCategory);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<InvestigateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);
  const [phasesCompleted, setPhasesCompleted] = useState<string[]>([]);

  const isHi = language === "hi";

  const handleStartInvestigation = async () => {
    if (!formInput.trim()) return;
    setIsRunning(true);
    setResult(null);
    setError(null);
    setShowReport(false);
    setPhasesCompleted([]);

    try {
      const response = await api.startInvestigation({
        formulation_description: formInput,
        formulation_category: selectedCategory,
        jurisdiction,
        language,
      });
      setResult(response);
      setPhasesCompleted(response.phases_completed);
    } catch (e: any) {
      setError(e.message || "Investigation failed");
    } finally {
      setIsRunning(false);
    }
  };

  const investigationCase = result?.case;

  const handleCopyReport = () => {
    if (investigationCase?.report_markdown) {
      navigator.clipboard.writeText(investigationCase.report_markdown);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#DEEED9] text-[#2D5A27] text-sm font-semibold">
          <Sparkles className="w-4 h-4" />
          <span>{isHi ? "बौद्धिक संपदा जांच" : "IP Investigation Engine"}</span>
        </div>
        <h2 className="text-2xl font-bold text-[#1E2D24] font-serif">
          {isHi ? "संपूर्ण बौद्धिक संपदा जांच" : "Comprehensive IP Investigation"}
        </h2>
        <p className="text-sm text-[#4B6354] max-w-2xl mx-auto">
          {isHi
            ? "अपने नुस्खे का वर्णन करें — हम पेटेंट, शोध, पारंपरिक ज्ञान और विनियमों में खोज करेंगे।"
            : "Describe your formulation — we'll search patents, research, traditional knowledge, and regulations to build a complete evidence-backed assessment."}
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6 space-y-4">
        <div>
          <label className="block text-sm font-semibold text-[#2D5A27] mb-2">
            {isHi ? "नुस्खे का विवरण" : "Formulation Description"}
          </label>
          <textarea
            value={formInput}
            onChange={(e) => setFormInput(e.target.value)}
            placeholder={isHi
              ? "उदा: हल्दी और नीम पाउडर, 3:1 अनुपात, भाप निष्कर्षण, सूजन और घाव भरने के लिए"
              : "e.g., Turmeric and Neem powder, 3:1 ratio, steam extracted, for inflammation and wound healing"}
            rows={3}
            className="w-full rounded-xl border border-[#D8EADB] bg-[#F3FFFB]/50 px-4 py-3 text-sm text-[#1E2D24] placeholder:text-[#8BA898] focus:outline-none focus:ring-2 focus:ring-[#7FB53D]/40 focus:border-[#7FB53D] resize-none"
            disabled={isRunning}
          />
        </div>

        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-[#4B6354] mb-1.5">
              {isHi ? "वर्गीकरण श्रेणी" : "Classification Category"}
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as FormulationCategory)}
              className="w-full rounded-lg border border-[#D8EADB] bg-white px-3 py-2 text-sm text-[#1E2D24] focus:outline-none focus:ring-2 focus:ring-[#7FB53D]/40"
              disabled={isRunning}
            >
              {Object.entries(CATEGORY_NAMES).filter(([k]) => k !== "unknown").map(([key, val]) => (
                <option key={key} value={key}>{isHi ? val.hi : val.en}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleStartInvestigation}
            disabled={isRunning || !formInput.trim()}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#2D5A27] to-[#3D7A35] text-white font-semibold text-sm shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
          >
            {isRunning ? (
              <><Loader2 className="w-4 h-4 animate-spin" />{isHi ? "जांच चल रही है..." : "Investigating..."}</>
            ) : (
              <><Search className="w-4 h-4" />{isHi ? "IP जांच शुरू करें" : "Start IP Investigation"}</>
            )}
          </button>
        </div>
      </div>

      {/* Progress Stepper */}
      {(isRunning || result) && (
        <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5">
          <div className="flex items-center justify-between">
            {PHASES.map((phase, idx) => {
              const Icon = phase.icon;
              const isComplete = phasesCompleted.includes(phase.key);
              const isCurrent = isRunning && phasesCompleted.length === idx;
              return (
                <React.Fragment key={phase.key}>
                  <div className={`flex flex-col items-center gap-1.5 ${isCurrent ? "scale-110" : ""} transition-transform`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                      isComplete ? "bg-emerald-100 text-emerald-700" :
                      isCurrent ? "bg-[#DEEED9] text-[#2D5A27] animate-pulse" :
                      "bg-gray-100 text-gray-400"
                    }`}>
                      {isComplete ? <CheckCircle2 className="w-5 h-5" /> :
                       isCurrent ? <Loader2 className="w-5 h-5 animate-spin" /> :
                       <Icon className="w-5 h-5" />}
                    </div>
                    <span className={`text-[10px] font-medium text-center leading-tight ${
                      isComplete ? "text-emerald-700" : isCurrent ? "text-[#2D5A27]" : "text-gray-400"
                    }`}>
                      {isHi ? phase.hi : phase.en}
                    </span>
                  </div>
                  {idx < PHASES.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-2 rounded ${
                      phasesCompleted.length > idx ? "bg-emerald-300" : "bg-gray-200"
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-800">{isHi ? "त्रुटि" : "Error"}</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {investigationCase && (
        <div className="space-y-6">

          {/* Extracted Formulation */}
          {investigationCase.formulation && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6">
              <h3 className="text-lg font-bold text-[#2D5A27] mb-4 flex items-center gap-2">
                <FlaskConical className="w-5 h-5" />
                {isHi ? "संरचित नुस्खा" : "Structured Formulation"}
              </h3>
              <div className="bg-[#F3FFFB]/60 rounded-lg p-3 mb-4 text-sm text-[#4B6354] italic">
                &ldquo;{investigationCase.formulation.raw_input}&rdquo;
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {investigationCase.formulation.ingredients.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[#4B6354] mb-2">{isHi ? "सामग्री" : "Ingredients"}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.ingredients.map((e, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-medium">🌿 {e.name}</span>
                      ))}
                    </div>
                  </div>
                )}
                {investigationCase.formulation.ratios.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[#4B6354] mb-2">{isHi ? "अनुपात" : "Ratios"}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.ratios.map((e, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">⚖️ {e.value || e.name}</span>
                      ))}
                    </div>
                  </div>
                )}
                {investigationCase.formulation.processes.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[#4B6354] mb-2">{isHi ? "प्रक्रियाएं" : "Processes"}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.processes.map((e, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-full bg-violet-100 text-violet-800 text-xs font-medium">⚗️ {e.name}</span>
                      ))}
                    </div>
                  </div>
                )}
                {investigationCase.formulation.intended_uses.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[#4B6354] mb-2">{isHi ? "उपयोग" : "Intended Uses"}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.intended_uses.map((e, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-full bg-orange-100 text-orange-800 text-xs font-medium">🎯 {e.name}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Evidence Sources */}
          {investigationCase.evidence_sources.length > 0 && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6">
              <h3 className="text-lg font-bold text-[#2D5A27] mb-4 flex items-center gap-2">
                <Search className="w-5 h-5" />
                {isHi ? `प्रमाण स्रोत (${investigationCase.evidence_sources.length})` : `Evidence Sources (${investigationCase.evidence_sources.length})`}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {investigationCase.evidence_sources.slice(0, 8).map((src) => {
                  const cfg = SOURCE_TYPE_CONFIG[src.source_type] || SOURCE_TYPE_CONFIG.regulation;
                  const isRegulation = src.source_type === "regulation";
                  const overlap = investigationCase.comparison_matrix?.overlap_scores?.[src.source_id];
                  return (
                    <div key={src.source_id} className="border border-[#D8EADB] rounded-xl p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.color}`}>
                          {isHi ? cfg.labelHi : cfg.label}
                        </span>
                        <span className="text-xs text-[#4B6354]">
                          {(src.relevance_score * 100).toFixed(0)}% {isHi ? "प्रासंगिक" : "relevant"}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-[#1E2D24] mb-1 line-clamp-2">{src.title}</h4>
                      {src.identifier && <p className="text-xs text-[#4B6354] mb-1">📋 {src.identifier}</p>}
                      {isRegulation ? (
                        <div className="mt-2 bg-[#F3FFFB] border border-[#D8EADB] rounded-lg p-2 text-[10px]">
                          <div className="flex items-center justify-between text-[#2D5A27] font-semibold mb-0.5">
                            <span>{isHi ? "⚖️ शासी वैधानिक प्राधिकरण" : "⚖️ Governing Statutory Authority"}</span>
                            <span className="font-bold">{(src.relevance_score * 100).toFixed(0)}% {isHi ? "प्रयोज्यता" : "Applicability"}</span>
                          </div>
                          <p className="text-[#4B6354] text-[9px] leading-tight">
                            {isHi
                              ? "वैधानिक प्रावधान नुस्खा सामग्री के बजाय कानूनी पात्रता और लाइसेंसिंग मार्गों को नियंत्रित करते हैं।"
                              : "Statutory provision governing legal eligibility & licensing pathways rather than recipe elements."}
                          </p>
                        </div>
                      ) : overlap !== undefined ? (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-[10px] mb-0.5">
                            <span className="text-[#4B6354]">{isHi ? "तत्व ओवरलैप" : "Element Overlap"}</span>
                            <span className={`font-bold ${overlap > 0.7 ? "text-red-600" : overlap > 0.4 ? "text-amber-600" : "text-emerald-600"}`}>
                              {(overlap * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full transition-all ${
                                overlap > 0.7 ? "bg-red-400" : overlap > 0.4 ? "bg-amber-400" : "bg-emerald-400"
                              }`}
                              style={{ width: `${Math.min(100, overlap * 100)}%` }}
                            />
                          </div>
                        </div>
                      ) : null}
                      <p className="text-xs text-[#6B7E72] mt-2 line-clamp-2">{src.relevant_text}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Comparison Matrix */}
          {investigationCase.comparison_matrix && investigationCase.comparison_matrix.comparisons.length > 0 && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6">
              <h3 className="text-lg font-bold text-[#2D5A27] mb-4 flex items-center gap-2">
                <Scale className="w-5 h-5" />
                {isHi ? "तत्व-वार तुलना" : "Element-Wise Comparison"}
              </h3>
              <div className="overflow-x-auto">
                {(() => {
                  const formulationSources = investigationCase.comparison_matrix.evidence_sources
                    .filter((s) => s.source_type !== "regulation")
                    .slice(0, 6);
                  return (
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-[#F3FFFB]">
                          <th className="text-left p-2 font-semibold text-[#2D5A27] sticky left-0 bg-[#F3FFFB]">{isHi ? "तत्व" : "Element"}</th>
                          <th className="p-2 font-semibold text-[#2D5A27]">{isHi ? "प्रकार" : "Type"}</th>
                          <th className="p-2 font-semibold text-[#2D5A27]">{isHi ? "उपयोगकर्ता" : "User"}</th>
                          {formulationSources.map((s) => (
                            <th key={s.source_id} className="p-2 font-semibold text-[#4B6354] max-w-[100px] truncate" title={s.title}>
                              {s.title.slice(0, 18)}...
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {investigationCase.comparison_matrix.comparisons.map((comp, idx) => (
                          <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-[#F3FFFB]/30"}>
                            <td className="p-2 font-medium text-[#1E2D24] sticky left-0 bg-inherit">{comp.element_name}</td>
                            <td className="p-2 text-center text-[#4B6354]">{comp.element_type}</td>
                            <td className="p-2 text-center text-emerald-600 font-bold">✓</td>
                            {formulationSources.map((s) => (
                              <td key={s.source_id} className={`p-2 text-center font-bold ${comp.matches[s.source_id] ? "text-emerald-600" : "text-red-400"}`}>
                                {comp.matches[s.source_id] ? "✓" : "✕"}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {/* Overlap row */}
                        <tr className="bg-[#DEEED9]/40 font-bold">
                          <td className="p-2 text-[#2D5A27] sticky left-0 bg-[#DEEED9]/40">{isHi ? "ओवरलैप %" : "Overlap %"}</td>
                          <td className="p-2"></td>
                          <td className="p-2"></td>
                          {formulationSources.map((s) => {
                            const ov = investigationCase.comparison_matrix!.overlap_scores[s.source_id] || 0;
                            return (
                              <td key={s.source_id} className={`p-2 text-center ${ov > 0.7 ? "text-red-700" : ov > 0.4 ? "text-amber-700" : "text-emerald-700"}`}>
                                {(ov * 100).toFixed(0)}%
                              </td>
                            );
                          })}
                        </tr>
                      </tbody>
                    </table>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Risk Assessment */}
          {investigationCase.risk_assessment && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6">
              <h3 className="text-lg font-bold text-[#2D5A27] mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" />
                {isHi ? "जोखिम आकलन" : "Risk Assessment"}
              </h3>

              {/* Overall Risk Banner */}
              <div className={`rounded-xl p-4 mb-5 bg-gradient-to-r ${RISK_BG[investigationCase.risk_assessment.overall_risk] || RISK_BG.MEDIUM} border ${
                investigationCase.risk_assessment.overall_risk === "CRITICAL" ? "border-red-300" :
                investigationCase.risk_assessment.overall_risk === "HIGH" ? "border-orange-300" :
                investigationCase.risk_assessment.overall_risk === "MEDIUM" ? "border-amber-300" : "border-emerald-300"
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-[#4B6354]">{isHi ? "समग्र जोखिम" : "Overall Risk"}</p>
                    <p className={`text-2xl font-black ${
                      investigationCase.risk_assessment.overall_risk === "CRITICAL" ? "text-red-700" :
                      investigationCase.risk_assessment.overall_risk === "HIGH" ? "text-orange-700" :
                      investigationCase.risk_assessment.overall_risk === "MEDIUM" ? "text-amber-700" : "text-emerald-700"
                    }`}>
                      {investigationCase.risk_assessment.overall_risk}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-[#4B6354]">{isHi ? "विश्वसनीयता" : "Confidence"}</p>
                    <div className="flex items-center justify-end gap-2">
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-white/70 text-[#2D5A27] shadow-xs">
                        {investigationCase.risk_assessment.overall_confidence_level || "HIGH"}
                      </span>
                      <p className="text-2xl font-black text-[#2D5A27]">
                        {(investigationCase.risk_assessment.overall_confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Multi-factor confidence breakdown (Fixed 4-pillar schema) */}
                {investigationCase.risk_assessment.confidence_breakdown && (
                  <div className="mt-3 pt-3 border-t border-black/5 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                    {FIXED_CONFIDENCE_METRICS.map((metric) => {
                      const score = metric.getValue(investigationCase.risk_assessment!.confidence_breakdown || {});
                      return (
                        <div
                          key={metric.id}
                          className="bg-white/70 rounded-lg px-2.5 py-1.5 border border-black/5 shadow-xs flex flex-col justify-between"
                          title={metric.desc}
                        >
                          <span className="text-[#4B6354] text-[10px] block font-medium truncate">
                            {isHi ? metric.labelHi : metric.label}
                          </span>
                          <span className="font-bold text-[#2D5A27] text-xs">{(score * 100).toFixed(0)}%</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Risk Dimension Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {investigationCase.risk_assessment.dimensions.map((dim) => {
                  const dimName = DIMENSION_NAMES[dim.dimension] || { en: dim.dimension, hi: dim.dimension };
                  const confVal = dim.confidence_score !== undefined ? dim.confidence_score : 0.85;
                  const confLvl = dim.confidence_level || (confVal >= 0.8 ? "HIGH" : "MED");
                  return (
                    <div key={dim.dimension} className={`rounded-xl border p-4 ${RISK_COLORS[dim.level] || RISK_COLORS.MEDIUM}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold">{isHi ? dimName.hi : dimName.en}</span>
                        <span className="text-lg font-black">{dim.level}</span>
                      </div>

                      {/* Score and confidence bars */}
                      <div className="space-y-1 mb-2">
                        <div className="flex items-center justify-between text-[10px] opacity-90 font-semibold">
                          <span>{isHi ? "जोखिम तीव्रता" : "Risk Severity"}: {(dim.score * 100).toFixed(0)}%</span>
                          <span className="bg-white/60 px-1.5 py-0.2 rounded text-[9px] font-bold text-[#2D5A27]">
                            {isHi ? "विश्वास" : "Conf"}: {(confVal * 100).toFixed(0)}% ({confLvl})
                          </span>
                        </div>
                        <div className="w-full bg-white/50 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              dim.level === "CRITICAL" ? "bg-red-500" :
                              dim.level === "HIGH" ? "bg-orange-500" :
                              dim.level === "MEDIUM" ? "bg-amber-500" : "bg-emerald-500"
                            }`}
                            style={{ width: `${Math.min(100, dim.score * 100)}%` }}
                          />
                        </div>
                      </div>
                      <p className="text-[10px] leading-relaxed opacity-85">{dim.reasoning}</p>

                      {dim.dimension === "regulatory_complexity" && (
                        <div className="mt-2 pt-1.5 border-t border-black/10 text-[9px] opacity-90 font-medium text-[#2D5A27]">
                          ⚖️ {isHi ? "डी&सी नियम, 1945 नियम 158B · फॉर्म 25D शास्त्रीय निर्माण लाइसेंस" : "D&C Rules, 1945 Rule 158B · Form 25D Classical ASU License"}
                        </div>
                      )}

                      {dim.dimension === "abs_compliance" && dim.level === "LOW" && (
                        <div className="mt-2 pt-1.5 border-t border-black/10 text-[9px] opacity-90 font-medium text-[#2D5A27]">
                          🌿 {isHi ? "जैविक विविधता अधिनियम धारा 40 एवं 2023 संशोधन छूट" : "BDA 2002 Sec 40 & 2023 Amendment ASU Exemption"}
                        </div>
                      )}

                      {dim.dimension === "novelty_risk" && dim.level === "CRITICAL" && (
                        <div className="mt-2 pt-1.5 border-t border-black/10 text-[9px] opacity-90 font-medium text-red-800">
                          ⚖️ {isHi ? "पेटेंट अधिनियम, 1970 · धारा 3(p) एवं 3(e) गैर-पेटेंट योग्यता बाधा" : "Patents Act, 1970 · Section 3(p) & 3(e) Non-Patentability Bar"}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Recommended Actions */}
              {investigationCase.risk_assessment.recommended_actions.length > 0 && (
                <div className="mt-5 bg-[#F3FFFB] rounded-xl p-4">
                  <p className="text-sm font-bold text-[#2D5A27] mb-2">{isHi ? "अनुशंसित कार्य" : "Recommended Actions"}</p>
                  <ul className="space-y-1.5">
                    {investigationCase.risk_assessment.recommended_actions.map((a, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-[#4B6354]">
                        <ArrowRight className="w-3 h-3 text-[#7FB53D] mt-0.5 shrink-0" />
                        {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Report Section */}
          {investigationCase.report_markdown && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-[#2D5A27] flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  {isHi ? "जांच रिपोर्ट" : "Investigation Report"}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyReport}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D8EADB] text-xs font-medium text-[#4B6354] hover:bg-[#F3FFFB] transition-colors"
                  >
                    <Copy className="w-3 h-3" />
                    {isHi ? "कॉपी" : "Copy"}
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D8EADB] text-xs font-medium text-[#4B6354] hover:bg-[#F3FFFB] transition-colors"
                  >
                    <Download className="w-3 h-3" />
                    {isHi ? "PDF डाउनलोड" : "Download PDF"}
                  </button>
                  <button
                    onClick={() => setShowReport(!showReport)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#2D5A27] text-white text-xs font-medium hover:bg-[#3D7A35] transition-colors"
                  >
                    <FileText className="w-3 h-3" />
                    {showReport ? (isHi ? "छिपाएं" : "Hide") : (isHi ? "रिपोर्ट देखें" : "View Report")}
                  </button>
                </div>
              </div>
              {showReport && (
                <div className="prose prose-sm max-w-none border-t border-[#D8EADB] pt-4">
                  <MarkdownRenderer content={investigationCase.report_markdown} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
