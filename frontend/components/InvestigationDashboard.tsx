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
  Sparkles,
  ArrowRight,
  Copy,
  Download,
  Check,
  BookOpen,
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

const SAMPLE_FORMULATIONS = [
  {
    titleEn: "Turmeric & Neem Wound Formulation",
    titleHi: "हल्दी एवं नीम व्रण रोपण",
    desc: "A traditional Ayurvedic formulation containing turmeric and neem in a 1:1 ratio, prepared as a decoction and intended for wound healing and skin inflammation. The formulation is based on ingredients and preparation methods described in classical Ayurvedic practice. I want to know whether there is any meaningful IP protection opportunity in India.",
    category: "classical_generic" as FormulationCategory,
    icon: "🌿",
  },
  {
    titleEn: "Classical Triphala Churna",
    titleHi: "शास्त्रीय त्रिफला चूर्ण",
    desc: "Triphala Churna formulation comprising equal parts of Haritaki (Terminalia chebula), Bibhitaki (Terminalia bellirica), and Amalaki (Phyllanthus emblica) prepared as a fine powder according to Sharangadhara Samhita for digestive support and metabolic balance.",
    category: "classical_generic" as FormulationCategory,
    icon: "🍃",
  },
  {
    titleEn: "Curcumin & Piperine Complex",
    titleHi: "करक्यूमिन एवं पिपेरिन संकुल",
    desc: "A synergistic phytopharmaceutical formulation comprising 95% standardized Curcuma longa extract and 1% Piper nigrum bioenhancer alkaloid prepared via solid dispersion tableting for severe osteoarthritis and cartilage regeneration.",
    category: "phytopharmaceutical" as FormulationCategory,
    icon: "✨",
  },
  {
    titleEn: "Neem & Aloe Wound Hydrogel",
    titleHi: "नीम एवं घृतकुमारी हाइड्रोजेल",
    desc: "A topical dermatological hydrogel patch loaded with cold-pressed Azadirachta indica oil and Aloe barbadensis inner gel encapsulated in hyaluronic acid micro-matrix for accelerated burn wound healing and scar prevention.",
    category: "patent_or_proprietary" as FormulationCategory,
    icon: "🔬",
  },
];

const RISK_COLORS: Record<string, string> = {
  LOW: "bg-emerald-50 text-emerald-800 border-emerald-200/80 shadow-2xs",
  MEDIUM: "bg-amber-50 text-amber-800 border-amber-200/80 shadow-2xs",
  HIGH: "bg-orange-50 text-orange-800 border-orange-200/80 shadow-2xs",
  CRITICAL: "bg-red-50 text-red-800 border-red-200/80 shadow-2xs",
};

const RISK_BG: Record<string, string> = {
  LOW: "from-emerald-50 to-emerald-100/60",
  MEDIUM: "from-amber-50 to-amber-100/60",
  HIGH: "from-orange-50 to-orange-100/60",
  CRITICAL: "from-red-50 to-red-100/60",
};

const SOURCE_TYPE_CONFIG: Record<string, { label: string; color: string; labelHi: string; icon: string }> = {
  patent: { label: "Patent", labelHi: "पेटेंट", color: "bg-blue-100 text-blue-800 border border-blue-200", icon: "📑" },
  research_paper: { label: "Research", labelHi: "शोध", color: "bg-purple-100 text-purple-800 border border-purple-200", icon: "🔬" },
  tk_source: { label: "Traditional Knowledge", labelHi: "पारंपरिक ज्ञान", color: "bg-amber-100 text-amber-800 border border-amber-200", icon: "📜" },
  formulation: { label: "Classical Formulation", labelHi: "शास्त्रीय नुस्खा", color: "bg-emerald-100 text-emerald-800 border border-emerald-200", icon: "🌿" },
  regulation: { label: "Regulation", labelHi: "विनियमन", color: "bg-green-100 text-green-800 border border-green-200", icon: "⚖️" },
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
  const [copied, setCopied] = useState(false);

  const isHi = language === "hi";

  const handleSelectSample = (sample: typeof SAMPLE_FORMULATIONS[0]) => {
    setFormInput(sample.desc);
    setSelectedCategory(sample.category);
  };

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
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePrint = () => {
    const prevTitle = document.title;
    const caseSuffix = investigationCase?.case_id ? `_${investigationCase.case_id}` : "";
    document.title = `IP_SAKTI_Investigation_Dossier${caseSuffix}`;
    window.print();
    setTimeout(() => {
      document.title = prevTitle;
    }, 1000);
  };

  return (
    <div className="max-w-5xl mx-auto w-full space-y-6 pb-12 print:max-w-none print:p-0 print:space-y-4 print:pb-0">
      {/* Print-Only Official Dossier Document Header */}
      {investigationCase && (
        <div className="hidden print:block mb-6 border-b-2 border-[#2D5A27] pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-[#2D5A27] text-white flex items-center justify-center font-bold text-2xl">
                🌿
              </div>
              <div>
                <h1 className="text-xl font-bold font-serif-luxury text-[#1E2D24] tracking-tight">
                  IP-SAKTI SAHAYAK
                </h1>
                <p className="text-[11px] font-bold text-[#2D5A27] tracking-wider uppercase">
                  {isHi
                    ? "आयुर्वेद बौद्धिक संपदा एवं विधिक अनुसंधान डोजियर"
                    : "Statutory Ayurvedic IP & Regulatory Intelligence Dossier"}
                </p>
              </div>
            </div>
            <div className="text-right text-[10px] text-gray-700 space-y-0.5">
              <p className="font-mono font-bold text-black text-xs">
                CASE REF: {investigationCase.case_id || "N/A"}
              </p>
              <p>
                Generated: {new Date().toLocaleDateString(isHi ? "hi-IN" : "en-IN", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-[#2D5A27] font-bold">
                Jurisdiction: {jurisdiction.toUpperCase()} (Patents Act 1970 · BDA 2002 · D&C Act 1940)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hero Header (Screen Only) */}
      <div className="text-center space-y-2 pt-2 print:hidden">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#DEEED9] text-[#2D5A27] text-xs font-bold border border-[#7FB53D]/30 shadow-2xs">
          <Sparkles className="w-3.5 h-3.5 text-[#7FB53D]" />
          <span>{isHi ? "बौद्धिक संपदा जांच इंजन" : "IP Investigation Engine"}</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight">
          {isHi ? "संपूर्ण बौद्धिक संपदा जांच" : "Comprehensive IP Investigation"}
        </h2>
        <p className="text-xs sm:text-sm text-[#4B6354] max-w-xl mx-auto leading-relaxed">
          {isHi
            ? "अपने नुस्खे का विवरण दें — हम पेटेंट, शोध, पारंपरिक ज्ञान (TKDL) और नियमों में संपूर्ण जांच करेंगे।"
            : "Describe your formulation — we'll search patents, research papers, classical treatises (TKDL), and statutory regulations to build an evidence-backed dossier."}
        </p>
      </div>

      {/* Quick Sample Presets (Screen Only) */}
      <div className="space-y-1.5 print:hidden">
        <span className="text-[11px] font-bold text-[#4B6354] uppercase tracking-wider block">
          {isHi ? "💡 त्वरित परीक्षण नुस्खे:" : "💡 Quick Sample Presets:"}
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {SAMPLE_FORMULATIONS.map((sample, idx) => {
            const isSelected = formInput.trim() === sample.desc.trim();
            return (
              <button
                key={idx}
                onClick={() => handleSelectSample(sample)}
                disabled={isRunning}
                className={`text-left p-2.5 rounded-xl border transition-all flex items-center justify-between group cursor-pointer disabled:opacity-50 ${
                  isSelected
                    ? "bg-[#DEEED9] border-[#2D5A27] shadow-xs"
                    : "bg-white hover:bg-[#F4F9F2] border-[#D8EADB] hover:border-[#7FB53D] shadow-2xs"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="text-base shrink-0">{sample.icon}</span>
                  <div className="truncate">
                    <p className="text-xs font-bold text-[#1E2D24] group-hover:text-[#2D5A27] truncate">
                      {isHi ? sample.titleHi : sample.titleEn}
                    </p>
                    <p className="text-[10px] text-[#6B7E72] truncate">
                      {CATEGORY_NAMES[sample.category][isHi ? "hi" : "en"]}
                    </p>
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#2D5A27] opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Formulation Input Card (Screen Only) */}
      <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-xs hover:shadow-sm transition-shadow p-5 sm:p-6 space-y-4 print:hidden">
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs sm:text-sm font-bold text-[#2D5A27] flex items-center gap-1.5">
              <FlaskConical className="w-4 h-4 text-[#7FB53D]" />
              {isHi ? "नुस्खे का विवरण एवं संयोजन" : "Formulation Description & Composition"}
            </label>
            <span className="text-[10px] text-[#6B7E72] font-medium">
              {formInput.length} {isHi ? "अक्षर" : "chars"}
            </span>
          </div>
          <textarea
            value={formInput}
            onChange={(e) => setFormInput(e.target.value)}
            placeholder={
              isHi
                ? "उदा: हल्दी और नीम पाउडर, 3:1 अनुपात, भाप निष्कर्षण, सूजन और घाव भरने के लिए..."
                : "e.g., A traditional Ayurvedic formulation containing turmeric and neem in a 1:1 ratio, prepared as a decoction and intended for wound healing..."
            }
            rows={4}
            className="w-full rounded-xl border border-[#D8EADB] bg-[#FAFDF9] focus:bg-white px-4 py-3 text-sm text-[#1E2D24] placeholder:text-[#8BA898] focus:outline-none focus:ring-2 focus:ring-[#7FB53D]/40 focus:border-[#7FB53D] transition-all leading-relaxed resize-y"
            disabled={isRunning}
          />
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-end justify-between gap-3 pt-1 border-t border-black/5">
          <div className="flex-1 min-w-[240px]">
            <label className="block text-xs font-semibold text-[#4B6354] mb-1.5 flex items-center gap-1">
              <Scale className="w-3.5 h-3.5 text-[#7FB53D]" />
              {isHi ? "वर्गीकरण श्रेणी" : "Classification Category"}
            </label>
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as FormulationCategory)}
                className="w-full appearance-none rounded-xl border border-[#D8EADB] bg-white px-3.5 py-2.5 text-xs sm:text-sm text-[#1E2D24] font-medium focus:outline-none focus:ring-2 focus:ring-[#7FB53D]/40 focus:border-[#7FB53D] cursor-pointer pr-10"
                disabled={isRunning}
              >
                {Object.entries(CATEGORY_NAMES)
                  .filter(([k]) => k !== "unknown")
                  .map(([key, val]) => (
                    <option key={key} value={key}>
                      {isHi ? val.hi : val.en}
                    </option>
                  ))}
              </select>
              <ChevronDown className="w-4 h-4 text-[#4B6354] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <button
            onClick={handleStartInvestigation}
            disabled={isRunning || !formInput.trim()}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#2D5A27] to-[#3D7A35] hover:from-[#3D7A35] hover:to-[#2D5A27] text-white font-bold text-xs sm:text-sm shadow-md shadow-[#2D5A27]/20 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] cursor-pointer shrink-0"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{isHi ? "जांच चल रही है..." : "Investigating..."}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-[#88C057]" />
                <span>{isHi ? "IP जांच शुरू करें" : "Start IP Investigation"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress Stepper (Screen Only) */}
      {(isRunning || result) && (
        <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-xs p-5 sm:p-6 animate-in fade-in duration-300 print:hidden">
          <div className="relative flex items-center justify-between">
            {/* Connecting Track Background */}
            <div className="absolute left-6 right-6 top-5 h-1 bg-[#DEEED9]/60 -z-0 rounded-full" />

            {/* Active Filled Progress Line */}
            <div
              className="absolute left-6 top-5 h-1 bg-gradient-to-r from-[#2D5A27] to-[#7FB53D] -z-0 rounded-full transition-all duration-500"
              style={{
                width: `calc(${Math.min(
                  100,
                  (Math.max(0, phasesCompleted.length) / (PHASES.length - 1)) * 100
                )}% - 2.5rem)`,
              }}
            />

            {PHASES.map((phase, idx) => {
              const Icon = phase.icon;
              const isComplete = phasesCompleted.includes(phase.key);
              const isCurrent = isRunning && phasesCompleted.length === idx;
              return (
                <div
                  key={phase.key}
                  className={`relative z-10 flex flex-col items-center gap-1.5 sm:gap-2 ${
                    isCurrent ? "scale-105" : ""
                  } transition-transform`}
                >
                  <div
                    className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center transition-all duration-300 font-bold text-xs shadow-2xs ${
                      isComplete
                        ? "bg-[#2D5A27] text-white ring-4 ring-[#DEEED9]"
                        : isCurrent
                        ? "bg-[#7FB53D] text-white ring-4 ring-[#7FB53D]/30 animate-pulse shadow-md"
                        : "bg-white text-gray-400 border-2 border-gray-200"
                    }`}
                  >
                    {isComplete ? (
                      <CheckCircle2 className="w-5 h-5 text-white" />
                    ) : isCurrent ? (
                      <Loader2 className="w-5 h-5 animate-spin text-white" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>
                  <div className="text-center max-w-[80px] sm:max-w-[110px]">
                    <span
                      className={`text-[10px] sm:text-[11px] font-bold block leading-tight ${
                        isComplete
                          ? "text-[#2D5A27]"
                          : isCurrent
                          ? "text-[#7FB53D]"
                          : "text-gray-400"
                      }`}
                    >
                      {isHi ? phase.hi : phase.en}
                    </span>
                    <span className="text-[9px] text-[#8BA898] font-medium hidden sm:block mt-0.5">
                      {isComplete
                        ? isHi
                          ? "पूर्ण"
                          : "Done"
                        : isCurrent
                        ? isHi
                          ? "सक्रिय..."
                          : "Active"
                        : `${idx + 1}/${PHASES.length}`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3 shadow-xs print:border-red-300 print:break-inside-avoid">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-bold text-red-800">{isHi ? "जांच त्रुटि" : "Investigation Error"}</p>
            <p className="text-xs text-red-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {investigationCase && (
        <div className="space-y-6 animate-in fade-in duration-400 print:space-y-4">
          {/* 1. Structured Formulation Card */}
          {investigationCase.formulation && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5 sm:p-6 space-y-4 print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-4">
              <div className="flex items-center justify-between pb-3 border-b border-black/5 print:border-gray-200">
                <h3 className="text-base sm:text-lg font-bold text-[#2D5A27] flex items-center gap-2 font-serif print:text-black">
                  <div className="w-7 h-7 rounded-lg bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center print:border print:border-gray-300">
                    <FlaskConical className="w-4 h-4" />
                  </div>
                  {isHi ? "संरचित नुस्खा विश्लेषण" : "Structured Formulation Analysis"}
                </h3>
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-[#F3FFFB] text-[#2D5A27] border border-[#D8EADB] print:border-gray-300 print:text-black">
                  {CATEGORY_NAMES[selectedCategory][isHi ? "hi" : "en"]}
                </span>
              </div>

              {/* Raw description quote */}
              <div className="bg-[#FAF8F2] border-l-4 border-[#7FB53D] rounded-r-xl p-3.5 text-xs sm:text-sm text-[#4B6354] italic leading-relaxed">
                &ldquo;{investigationCase.formulation.raw_input}&rdquo;
              </div>

              {/* Extracted Entity Matrix */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
                {investigationCase.formulation.ingredients.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider flex items-center gap-1">
                      🌿 {isHi ? "सामग्री (Ingredients)" : "Ingredients"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.ingredients.map((e, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold shadow-2xs"
                        >
                          {e.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {investigationCase.formulation.ratios.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider flex items-center gap-1">
                      ⚖️ {isHi ? "अनुपात (Ratios)" : "Ratios & Weights"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.ratios.map((e, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 text-xs font-semibold shadow-2xs"
                        >
                          {e.value || e.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {investigationCase.formulation.processes.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider flex items-center gap-1">
                      ⚗️ {isHi ? "प्रक्रियाएं (Processes)" : "Extraction & Processes"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.processes.map((e, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-purple-50 text-purple-800 border border-purple-200 text-xs font-semibold shadow-2xs"
                        >
                          {e.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {investigationCase.formulation.intended_uses.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider flex items-center gap-1">
                      🎯 {isHi ? "उपयोग (Indication)" : "Intended Indications"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {investigationCase.formulation.intended_uses.map((e, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold shadow-2xs"
                        >
                          {e.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 2. Evidence Sources Card */}
          {investigationCase.evidence_sources.length > 0 && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5 sm:p-6 space-y-4 print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-4">
              <div className="flex items-center justify-between pb-3 border-b border-black/5 print:border-gray-200">
                <h3 className="text-base sm:text-lg font-bold text-[#2D5A27] flex items-center gap-2 font-serif print:text-black">
                  <div className="w-7 h-7 rounded-lg bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center print:border print:border-gray-300">
                    <Search className="w-4 h-4" />
                  </div>
                  {isHi
                    ? `खोजे गए प्रमाण स्रोत (${investigationCase.evidence_sources.length})`
                    : `Discovered Prior Art & Regulatory Sources (${investigationCase.evidence_sources.length})`}
                </h3>
                <span className="text-xs text-[#4B6354] font-medium hidden sm:inline print:inline print:text-gray-600">
                  {isHi ? "बहु-स्रोत प्रमाण आधार" : "Multi-Corpus Cross Retrieval"}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 print:grid-cols-2 print:gap-3">
                {investigationCase.evidence_sources.slice(0, 8).map((src) => {
                  const cfg = SOURCE_TYPE_CONFIG[src.source_type] || SOURCE_TYPE_CONFIG.regulation;
                  const isRegulation = src.source_type === "regulation";
                  const overlap = investigationCase.comparison_matrix?.overlap_scores?.[src.source_id];
                  return (
                    <div
                      key={src.source_id}
                      className="border border-[#D8EADB] hover:border-[#7FB53D]/80 rounded-xl p-4 hover:shadow-md transition-all bg-white flex flex-col justify-between print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-3"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${cfg.color} print:border-gray-300`}>
                            {cfg.icon} {isHi ? cfg.labelHi : cfg.label}
                          </span>
                          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-[#F3FFFB] text-[#2D5A27] print:border print:border-gray-300 print:text-black">
                            {(src.relevance_score * 100).toFixed(0)}% {isHi ? "प्रासंगिकता" : "Relevance"}
                          </span>
                        </div>
                        <h4 className="text-xs sm:text-sm font-bold text-[#1E2D24] mb-1 line-clamp-2 leading-snug print:line-clamp-none print:text-black">
                          {src.title}
                        </h4>
                        {src.identifier && (
                          <p className="text-[11px] font-mono text-[#4B6354] mb-1.5 print:text-gray-700">📋 {src.identifier}</p>
                        )}
                        <p className="text-xs text-[#6B7E72] line-clamp-2 leading-relaxed print:line-clamp-none print:text-gray-800">{src.relevant_text}</p>
                      </div>

                      {isRegulation ? (
                        <div className="mt-3 bg-[#F3FFFB] border border-[#D8EADB] rounded-lg p-2.5 text-[10px] print:bg-gray-50 print:border-gray-300">
                          <div className="flex items-center justify-between text-[#2D5A27] font-bold mb-0.5 print:text-black">
                            <span>{isHi ? "⚖️ शासी वैधानिक प्राधिकरण" : "⚖️ Statutory Regulatory Authority"}</span>
                            <span className="font-bold">
                              {(src.relevance_score * 100).toFixed(0)}% {isHi ? "प्रयोज्यता" : "Applicability"}
                            </span>
                          </div>
                          <p className="text-[#4B6354] text-[9px] leading-tight print:text-gray-600">
                            {isHi
                              ? "वैधानिक प्रावधान नुस्खा सामग्री के बजाय कानूनी पात्रता और लाइसेंसिंग मार्गों को नियंत्रित करते हैं।"
                              : "Statutory provision governing legal eligibility & licensing pathways rather than recipe elements."}
                          </p>
                        </div>
                      ) : overlap !== undefined ? (
                        <div className="mt-3 pt-2 border-t border-black/5 print:border-gray-200">
                          <div className="flex items-center justify-between text-[11px] mb-1 font-semibold">
                            <span className="text-[#4B6354] print:text-gray-700">{isHi ? "तत्व ओवरलैप:" : "Element Overlap:"}</span>
                            <span
                              className={`font-bold ${
                                overlap > 0.7
                                  ? "text-red-600"
                                  : overlap > 0.4
                                  ? "text-amber-600"
                                  : "text-emerald-600"
                              }`}
                            >
                              {(overlap * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden print:border print:border-gray-300">
                            <div
                              className={`h-1.5 rounded-full transition-all duration-500 ${
                                overlap > 0.7 ? "bg-red-500" : overlap > 0.4 ? "bg-amber-500" : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(100, overlap * 100)}%` }}
                            />
                          </div>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 3. Comparison Matrix */}
          {investigationCase.comparison_matrix && investigationCase.comparison_matrix.comparisons.length > 0 && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5 sm:p-6 space-y-4 print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-4">
              <div className="flex items-center justify-between pb-3 border-b border-black/5 print:border-gray-200">
                <h3 className="text-base sm:text-lg font-bold text-[#2D5A27] flex items-center gap-2 font-serif print:text-black">
                  <div className="w-7 h-7 rounded-lg bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center print:border print:border-gray-300">
                    <Scale className="w-4 h-4" />
                  </div>
                  {isHi ? "तत्व-वार पूर्व कला तुलना मैट्रिक्स" : "Element-Wise Prior Art Comparison Matrix"}
                </h3>
              </div>

              <div className="overflow-x-auto rounded-xl border border-[#D8EADB] print:border-gray-300 print:break-inside-avoid">
                {(() => {
                  const formulationSources = investigationCase.comparison_matrix.evidence_sources
                    .filter((s) => s.source_type !== "regulation")
                    .slice(0, 6);
                  return (
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-[#F3FFFB] border-b border-[#D8EADB] print:bg-gray-100 print:border-gray-300">
                          <th className="text-left p-3 font-bold text-[#2D5A27] sticky left-0 bg-[#F3FFFB] print:bg-gray-100 print:text-black">
                            {isHi ? "नुस्खा तत्व" : "Formulation Element"}
                          </th>
                          <th className="p-3 font-bold text-[#2D5A27] text-center print:text-black">{isHi ? "प्रकार" : "Type"}</th>
                          <th className="p-3 font-bold text-[#2D5A27] text-center print:text-black">{isHi ? "उपयोगकर्ता" : "User"}</th>
                          {formulationSources.map((s) => (
                            <th
                              key={s.source_id}
                              className="p-3 font-bold text-[#4B6354] max-w-[130px] truncate text-center print:text-black"
                              title={s.title}
                            >
                              {s.title.slice(0, 20)}...
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D8EADB]/50 print:divide-gray-200">
                        {investigationCase.comparison_matrix.comparisons.map((comp, idx) => (
                          <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-[#F3FFFB]/25 print:bg-gray-50/50"}>
                            <td className="p-3 font-semibold text-[#1E2D24] sticky left-0 bg-inherit whitespace-nowrap print:text-black">
                              {comp.element_name}
                            </td>
                            <td className="p-3 text-center text-[#4B6354] uppercase text-[10px] font-bold print:text-gray-700">
                              {comp.element_type}
                            </td>
                            <td className="p-3 text-center">
                              <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 font-bold inline-flex items-center justify-center text-xs print:border print:border-emerald-300">
                                ✓
                              </span>
                            </td>
                            {formulationSources.map((s) => (
                              <td key={s.source_id} className="p-3 text-center">
                                {comp.matches[s.source_id] ? (
                                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 font-bold inline-flex items-center justify-center text-xs print:border print:border-emerald-300">
                                    ✓
                                  </span>
                                ) : (
                                  <span className="w-5 h-5 rounded-full bg-red-100 text-red-500 font-bold inline-flex items-center justify-center text-xs print:border print:border-red-300">
                                    ✕
                                  </span>
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {/* Overlap Summary Row */}
                        <tr className="bg-[#DEEED9]/50 font-bold border-t-2 border-[#D8EADB] print:bg-gray-100 print:border-gray-300">
                          <td className="p-3 text-[#2D5A27] sticky left-0 bg-[#DEEED9]/50 print:bg-gray-100 print:text-black">
                            {isHi ? "कुल ओवरलैप %" : "Total Overlap %"}
                          </td>
                          <td className="p-3"></td>
                          <td className="p-3 text-center text-[#2D5A27] font-black print:text-black">100%</td>
                          {formulationSources.map((s) => {
                            const ov = investigationCase.comparison_matrix!.overlap_scores[s.source_id] || 0;
                            return (
                              <td
                                key={s.source_id}
                                className={`p-3 text-center font-black ${
                                  ov > 0.7 ? "text-red-700" : ov > 0.4 ? "text-amber-700" : "text-emerald-700"
                                }`}
                              >
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

          {/* 4. Risk Assessment & Calibrated Metrics */}
          {investigationCase.risk_assessment && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5 sm:p-6 space-y-5 print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-4">
              <div className="flex items-center justify-between pb-3 border-b border-black/5 print:border-gray-200">
                <h3 className="text-base sm:text-lg font-bold text-[#2D5A27] flex items-center gap-2 font-serif print:text-black">
                  <div className="w-7 h-7 rounded-lg bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center print:border print:border-gray-300">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  {isHi ? "5-आयामी IP एवं विधिक जोखिम आकलन" : "5-Dimension IP & Statutory Risk Assessment"}
                </h3>
              </div>

              {/* Overall Risk Banner */}
              <div
                className={`rounded-2xl p-5 bg-gradient-to-r ${
                  RISK_BG[investigationCase.risk_assessment.overall_risk] || RISK_BG.MEDIUM
                } border ${
                  investigationCase.risk_assessment.overall_risk === "CRITICAL"
                    ? "border-red-300"
                    : investigationCase.risk_assessment.overall_risk === "HIGH"
                    ? "border-orange-300"
                    : investigationCase.risk_assessment.overall_risk === "MEDIUM"
                    ? "border-amber-300"
                    : "border-emerald-300"
                } shadow-sm print:shadow-none print:break-inside-avoid`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider print:text-gray-700">
                      {isHi ? "समग्र पेटेंट एवं विधिक जोखिम" : "Overall IP Protection Risk"}
                    </p>
                    <p
                      className={`text-2xl sm:text-3xl font-black tracking-tight ${
                        investigationCase.risk_assessment.overall_risk === "CRITICAL"
                          ? "text-red-700"
                          : investigationCase.risk_assessment.overall_risk === "HIGH"
                          ? "text-orange-700"
                          : investigationCase.risk_assessment.overall_risk === "MEDIUM"
                          ? "text-amber-700"
                          : "text-emerald-700"
                      }`}
                    >
                      {investigationCase.risk_assessment.overall_risk}
                    </p>
                  </div>
                  <div className="text-left sm:text-right">
                    <p className="text-xs font-bold text-[#4B6354] uppercase tracking-wider print:text-gray-700">
                      {isHi ? "आकलन विश्वसनीयता (Confidence)" : "Assessment Confidence"}
                    </p>
                    <div className="flex items-center sm:justify-end gap-2 mt-0.5">
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-white text-[#2D5A27] shadow-2xs border border-black/5 print:border-gray-300 print:text-black">
                        {investigationCase.risk_assessment.overall_confidence_level || "HIGH"}
                      </span>
                      <p className="text-2xl sm:text-3xl font-black text-[#2D5A27] print:text-black">
                        {(investigationCase.risk_assessment.overall_confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Multi-factor confidence breakdown (Fixed 4-pillar schema) */}
                {investigationCase.risk_assessment.confidence_breakdown && (
                  <div className="mt-4 pt-3.5 border-t border-black/10 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] print:border-gray-300">
                    {FIXED_CONFIDENCE_METRICS.map((metric) => {
                      const score = metric.getValue(investigationCase.risk_assessment!.confidence_breakdown || {});
                      return (
                        <div
                          key={metric.id}
                          className="bg-white/80 backdrop-blur-xs rounded-xl px-3 py-2 border border-black/5 shadow-2xs flex flex-col justify-between print:border-gray-300 print:bg-white"
                          title={metric.desc}
                        >
                          <span className="text-[#4B6354] text-[10px] block font-bold truncate print:text-gray-700">
                            {isHi ? metric.labelHi : metric.label}
                          </span>
                          <span className="font-black text-[#2D5A27] text-sm mt-0.5 print:text-black">
                            {(score * 100).toFixed(0)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* 5 Risk Dimension Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 print:grid-cols-2 print:gap-3">
                {investigationCase.risk_assessment.dimensions.map((dim) => {
                  const dimName = DIMENSION_NAMES[dim.dimension] || { en: dim.dimension, hi: dim.dimension };
                  const confVal = dim.confidence_score !== undefined ? dim.confidence_score : 0.85;
                  const confLvl = dim.confidence_level || (confVal >= 0.8 ? "HIGH" : "MED");
                  return (
                    <div
                      key={dim.dimension}
                      className={`rounded-xl border p-4 flex flex-col justify-between print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-3 ${
                        RISK_COLORS[dim.level] || RISK_COLORS.MEDIUM
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold text-[#1E2D24] print:text-black">
                            {isHi ? dimName.hi : dimName.en}
                          </span>
                          <span className="text-sm font-black px-2 py-0.5 rounded bg-white/70 shadow-2xs print:border print:border-gray-300 print:text-black">
                            {dim.level}
                          </span>
                        </div>

                        {/* Dual Score Bars */}
                        <div className="space-y-1 mb-2.5">
                          <div className="flex items-center justify-between text-[10px] opacity-90 font-semibold">
                            <span>
                              {isHi ? "जोखिम तीव्रता" : "Risk Severity"}: {(dim.score * 100).toFixed(0)}%
                            </span>
                            <span className="bg-white/80 px-1.5 py-0.2 rounded text-[9px] font-bold text-[#2D5A27] print:border print:border-gray-300 print:text-black">
                              {isHi ? "विश्वास" : "Conf"}: {(confVal * 100).toFixed(0)}% ({confLvl})
                            </span>
                          </div>
                          <div className="w-full bg-white/70 rounded-full h-2 overflow-hidden print:border print:border-gray-300">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${
                                dim.level === "CRITICAL"
                                  ? "bg-red-500"
                                  : dim.level === "HIGH"
                                  ? "bg-orange-500"
                                  : dim.level === "MEDIUM"
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(100, dim.score * 100)}%` }}
                            />
                          </div>
                        </div>
                        <p className="text-[11px] leading-relaxed opacity-90 text-[#2C3E32] print:text-black">{dim.reasoning}</p>
                      </div>

                      {/* Statutory Citation Banner per dimension */}
                      <div className="mt-3 pt-2 border-t border-black/10 print:border-gray-300">
                        {dim.dimension === "novelty_risk" && (dim.level === "CRITICAL" || dim.level === "HIGH") && (
                          <div className="text-[10px] font-bold text-red-900">
                            ⚖️ {isHi ? "पेटेंट अधिनियम, 1970 · धारा 3(p) एवं 3(e) गैर-पेटेंट योग्यता बाधा" : "Patents Act, 1970 · Section 3(p) & 3(e) Non-Patentability Bar"}
                          </div>
                        )}
                        {dim.dimension === "novelty_risk" && (dim.level === "LOW" || dim.level === "MEDIUM") && (
                          <div className="text-[10px] font-bold text-emerald-900">
                            ⚖️ {isHi ? "पेटेंट अधिनियम, 1970 · धारा 2(1)(j) नवीनता एवं आविष्कारशीलता" : "Patents Act, 1970 · Section 2(1)(j) Novelty & Inventive Step"}
                          </div>
                        )}

                        {dim.dimension === "tk_overlap" && (dim.level === "CRITICAL" || dim.level === "HIGH") && (
                          <div className="text-[10px] font-bold text-red-900">
                            📜 {isHi ? "डी&सी अधिनियम, 1940 प्रथम अनुसूची ग्रंथ एवं टीकेडीएल पूर्व कला" : "D&C Act, 1940 First Schedule Treatises & TKDL Prior Art"}
                          </div>
                        )}
                        {dim.dimension === "tk_overlap" && (dim.level === "LOW" || dim.level === "MEDIUM") && (
                          <div className="text-[10px] font-bold text-[#2D5A27]">
                            📜 {isHi ? "शास्त्रीय ग्रंथों में अप्रलेखित संयोजन" : "Undocumented Combination in First Schedule Treatises"}
                          </div>
                        )}

                        {dim.dimension === "regulatory_complexity" && dim.level === "LOW" && (
                          <div className="text-[10px] font-bold text-[#2D5A27]">
                            ⚖️ {isHi ? "डी&सी नियम, 1945 नियम 158B · फॉर्म 25D शास्त्रीय निर्माण लाइसेंस" : "D&C Rules, 1945 Rule 158B · Form 25D Classical ASU License"}
                          </div>
                        )}
                        {dim.dimension === "regulatory_complexity" && (dim.level === "CRITICAL" || dim.level === "HIGH") && (
                          <div className="text-[10px] font-bold text-orange-950">
                            ⚖️ {isHi ? "डी&सी नियम, 1945 नियम 122E / अनुसूची Y · नैदानिक परीक्षण डोजियर" : "D&C Rules, 1945 Rule 122E / Schedule Y · Clinical Trial Dossier Required"}
                          </div>
                        )}

                        {dim.dimension === "abs_compliance" && dim.level === "LOW" && (
                          <div className="text-[10px] font-bold text-[#2D5A27]">
                            🌿 {isHi ? "जैविक विविधता अधिनियम धारा 40 एवं 2023 संशोधन छूट" : "BDA 2002 Sec 40 & 2023 Amendment ASU Exemption"}
                          </div>
                        )}
                        {dim.dimension === "abs_compliance" && (dim.level === "CRITICAL" || dim.level === "HIGH") && (
                          <div className="text-[10px] font-bold text-orange-950">
                            🌿 {isHi ? "जैविक विविधता अधिनियम धारा 6 एवं NBA फॉर्म III अनिवार्य" : "BDA 2002 Section 6 · Mandatory NBA Form III Prior Approval"}
                          </div>
                        )}

                        {dim.dimension === "prior_art_exposure" && (dim.level === "CRITICAL" || dim.level === "HIGH") && (
                          <div className="text-[10px] font-bold text-red-900">
                            🔬 {isHi ? "वैज्ञानिक साहित्य एवं ऐतिहासिक सीएसआईआर निरस्तीकरण मिसालें" : "Scientific Literature & Landmark CSIR Revocation Precedents"}
                          </div>
                        )}
                        {dim.dimension === "prior_art_exposure" && (dim.level === "LOW" || dim.level === "MEDIUM") && (
                          <div className="text-[10px] font-bold text-[#2D5A27]">
                            🔬 {isHi ? "सार्वजनिक प्रक्षेत्र में सीमित साहित्य प्रकटीकरण" : "Limited Prior Art Disclosures in Public Domain"}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Recommended Strategic Actions */}
              {investigationCase.risk_assessment.recommended_actions.length > 0 && (
                <div className="bg-[#F3FFFB] rounded-xl p-4 sm:p-5 border border-[#D8EADB] print:border-gray-300 print:shadow-none print:break-inside-avoid print:bg-gray-50/70">
                  <p className="text-xs sm:text-sm font-bold text-[#2D5A27] mb-2.5 flex items-center gap-2 print:text-black">
                    <CheckCircle2 className="w-4 h-4 text-[#7FB53D] print:text-black" />
                    {isHi ? "रणनीतिक अनुशंसित कार्य योजना" : "Strategic Recommended Action Plan"}
                  </p>
                  <ul className="space-y-2">
                    {investigationCase.risk_assessment.recommended_actions.map((a, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-[#2C4A36] leading-relaxed print:text-black">
                        <span className="w-4 h-4 rounded-full bg-[#DEEED9] text-[#2D5A27] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5 print:border print:border-gray-300 print:bg-gray-100 print:text-black">
                          {i + 1}
                        </span>
                        <span>{a}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* 5. Comprehensive Dossier / Investigation Report */}
          {investigationCase.report_markdown && (
            <div className="bg-white rounded-2xl border border-[#D8EADB] shadow-sm p-5 sm:p-6 space-y-4 print:border-gray-300 print:shadow-none print:break-inside-avoid print:p-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-black/5 print:border-gray-200">
                <h3 className="text-base sm:text-lg font-bold text-[#2D5A27] flex items-center gap-2 font-serif print:text-black">
                  <div className="w-7 h-7 rounded-lg bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center print:border print:border-gray-300">
                    <FileText className="w-4 h-4" />
                  </div>
                  {isHi ? "आधिकारिक विधिक एवं आईपी जांच डोजियर" : "Official IP & Regulatory Investigation Dossier"}
                </h3>
                <div className="flex items-center gap-2 print:hidden">
                  <button
                    onClick={handleCopyReport}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D8EADB] text-xs font-semibold text-[#4B6354] hover:bg-[#F3FFFB] hover:text-[#1E2D24] transition-colors cursor-pointer"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? (isHi ? "कॉपी हो गया!" : "Copied!") : (isHi ? "कॉपी करें" : "Copy Markdown")}
                  </button>
                  <button
                    onClick={handlePrint}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D8EADB] text-xs font-semibold text-[#4B6354] hover:bg-[#F3FFFB] hover:text-[#1E2D24] transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    {isHi ? "प्रिंट / PDF" : "Print / PDF"}
                  </button>
                  <button
                    onClick={() => setShowReport(!showReport)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#2D5A27] hover:bg-[#3D7A35] text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    {showReport
                      ? isHi
                        ? "डोजियर छिपाएं"
                        : "Hide Full Dossier"
                      : isHi
                      ? "संपूर्ण डोजियर देखें"
                      : "View Full Dossier"}
                  </button>
                </div>
              </div>
              <div className={`prose prose-sm max-w-none border-t border-[#D8EADB] print:border-gray-300 pt-4 animate-in fade-in duration-300 ${showReport ? "block" : "hidden print:block"}`}>
                <MarkdownRenderer content={investigationCase.report_markdown} />
              </div>
            </div>
          )}

          {/* Print-Only Official Dossier Document Footer */}
          <div className="hidden print:block mt-8 pt-4 border-t border-gray-300 text-center text-[9px] text-gray-600 print:break-inside-avoid">
            <p className="font-bold text-gray-800">
              CONFIDENTIAL & PRIVILEGED STATUTORY REPORT — Generated by IP-SAKTI Sahayak (Ayurveda IP & Regulatory Intelligence Engine)
            </p>
            <p className="mt-0.5 text-gray-600">
              Statutory Framework: The Patents Act 1970 (Sec 3(p), 3(e), 2(1)(j)) · Biological Diversity Act 2002 (Sec 3, 6, 40) · Drugs & Cosmetics Rules 1945 (Rule 122E, Rule 158B) · TKDL Prior Art Library.
            </p>
            <p className="mt-0.5 text-gray-500">
              This dossier is an AI-assisted preliminary statutory and prior art screening document. Formal patent and regulatory filings require review by a registered patent agent or qualified legal counsel.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
