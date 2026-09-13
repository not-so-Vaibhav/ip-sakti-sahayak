"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, CitationItem, FormulationCategory, QueryResponse } from "@/lib/api";
import { translations, PRESET_QUERIES, PresetQuery } from "@/lib/translations";
import { AnswerCard } from "./AnswerCard";
import { AbstentionCard } from "./AbstentionCard";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Clock,
  CheckCircle2,
  RefreshCw,
  Filter,
  ShieldAlert,
  Loader2,
  ChevronDown,
  Leaf,
} from "lucide-react";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text?: string;
  response?: QueryResponse;
  timestamp: string;
}

interface ChatInterfaceProps {
  language: "en" | "hi";
  jurisdiction: "india" | "international";
  activeCategory: FormulationCategory;
  onSelectCategory: (cat: FormulationCategory) => void;
  onOpenCitation: (citation: CitationItem) => void;
  onOpenFacilitator: (initialQuery?: string) => void;
  initialQuery?: string;
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

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  language,
  jurisdiction,
  activeCategory,
  onSelectCategory,
  onOpenCitation,
  onOpenFacilitator,
  initialQuery,
}) => {
  const t = translations[language].chat;

  const [inputQuery, setInputQuery] = useState(initialQuery || "");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<FormulationCategory>(activeCategory);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync prop changes
  useEffect(() => {
    setSelectedCategory(activeCategory);
  }, [activeCategory]);

  useEffect(() => {
    if (initialQuery) {
      setInputQuery(initialQuery);
    }
  }, [initialQuery]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, loadingStepIndex]);

  // Progressive Loading State Timer & Status Ticker
  useEffect(() => {
    if (isLoading) {
      setElapsedSeconds(0);
      setLoadingStepIndex(0);

      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          if (next === 3) setLoadingStepIndex(1);
          if (next === 7) setLoadingStepIndex(2);
          if (next === 13) setLoadingStepIndex(3);
          if (next === 22) setLoadingStepIndex(4);
          return next;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isLoading]);

  const handleSendQuery = async (queryToSubmit?: string, catOverride?: FormulationCategory) => {
    const text = (queryToSubmit || inputQuery).trim();
    if (!text || isLoading) return;

    const effectiveCat = catOverride || selectedCategory;
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Add user message to stream
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: text,
      timestamp: now,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await api.submitQuery({
        query_text: text,
        jurisdiction: jurisdiction,
        formulation_category: effectiveCat,
        language: language,
      });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        response: response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Query submission error:", err);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: "assistant",
        response: {
          query_id: "error",
          query_text: text,
          jurisdiction: jurisdiction,
          formulation_category: effectiveCat,
          language: language,
          answer: null,
          citations: [],
          confidence_score: 0.0,
          abstained: true,
          abstention_reason: `Connection error: ${err.message || "Failed to reach backend service."}`,
          escalation_offered: true,
          generation_attempts: 0,
        },
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePresetClick = (preset: PresetQuery) => {
    setSelectedCategory(preset.category);
    onSelectCategory(preset.category);
    handleSendQuery(preset.query_text, preset.category);
  };

  const currentPresets = PRESET_QUERIES[language] || PRESET_QUERIES.en;

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-6 px-3 sm:px-6 flex flex-col h-full space-y-4">
      {/* Category Filter & Scope Banner */}
      <div className="ayur-card p-3 sm:p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-3 w-full">
        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 shrink-0">
            <Filter className="w-3.5 h-3.5 text-[#7FB53D]" />
            <span className="text-[11px] sm:text-xs font-bold text-[#1E2D24] uppercase tracking-wide">
              {t.categoryFilterLabel}
            </span>
          </div>
          <div className="relative flex-1 sm:flex-none min-w-[180px]">
            <select
              value={selectedCategory}
              onChange={(e) => {
                const cat = e.target.value as FormulationCategory;
                setSelectedCategory(cat);
                onSelectCategory(cat);
              }}
              className="w-full appearance-none bg-[#DEEED9]/60 hover:bg-[#DEEED9] text-[#2D5A27] font-bold text-xs pl-3 pr-8 py-1.5 rounded-xl border border-[#7FB53D]/30 focus:outline-none focus:ring-2 focus:ring-[#7FB53D] cursor-pointer transition-colors"
            >
              {Object.entries(CATEGORY_NAMES).map(([key, name]) => (
                <option key={key} value={key}>
                  {language === "hi" ? name.hi : name.en}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#2D5A27] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] sm:text-xs text-[#4B6354]">
          <span className="font-semibold text-[#2D5A27]">
            {jurisdiction === "india" ? "🇮🇳 Indian Law Corpus" : "🌐 International Context"}
          </span>
        </div>
      </div>

      {/* Chat History Container */}
      <div className="flex-1 overflow-y-auto space-y-6 min-h-[360px]">
        {/* Empty State / Welcome Screen */}
        {messages.length === 0 && (
          <div className="py-8 sm:py-12 text-center space-y-6">
            <div className="w-16 h-16 rounded-3xl bg-[#DEEED9] border border-[#7FB53D]/30 flex items-center justify-center mx-auto text-[#7FB53D] shadow-sm">
              <Leaf className="w-8 h-8 animate-pulse-subtle" />
            </div>

            <div className="space-y-2 max-w-lg mx-auto">
              <h2 className="text-2xl sm:text-3xl font-serif-luxury font-bold text-[#1E2D24]">
                {t.headerTitle}
              </h2>
              <p className="text-xs sm:text-sm text-[#4B6354]">
                {language === "hi"
                  ? "नीचे दिए गए किसी भी उदाहरण पर क्लिक करें या अपना प्रश्न दर्ज करें:"
                  : "Ask any legal, biodiversity ABS, or regulatory question to see verified statutory grounding:"}
              </p>
            </div>

            {/* Quick-Prompt Presets */}
            <div className="max-w-2xl mx-auto space-y-3 pt-2">
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-[#7FB53D] uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t.presetHeader}</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                {currentPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetClick(preset)}
                    className="p-3.5 rounded-2xl bg-white hover:bg-[#DEEED9]/40 border border-[#D8EADB] hover:border-[#7FB53D]/50 transition-all text-left shadow-xs hover:shadow-md group"
                  >
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/20 inline-block mb-1.5">
                      {preset.tag}
                    </span>
                    <p className="text-xs font-semibold text-[#1E2D24] group-hover:text-[#2D5A27] line-clamp-2">
                      &ldquo;{preset.query_text}&rdquo;
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === "user" ? "items-end" : "items-start"
            } space-y-1.5`}
          >
            {/* Sender Label */}
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#4B6354] px-1">
              {msg.sender === "user" ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3" />
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-[#7FB53D]" />
                  <span>IP-SAKTI Sahayak</span>
                </>
              )}
              <span className="text-slate-400 font-normal">• {msg.timestamp}</span>
            </div>

            {/* Message Bubble / Component */}
            {msg.sender === "user" ? (
              <div className="p-4 rounded-2xl rounded-tr-xs bg-[#7FB53D] text-white max-w-xl text-sm font-medium shadow-sm leading-relaxed">
                {msg.text}
              </div>
            ) : msg.response?.abstained ? (
              <div className="w-full max-w-3xl">
                <AbstentionCard
                  response={msg.response}
                  language={language}
                  onOpenFacilitator={() => onOpenFacilitator(msg.response?.query_text)}
                />
              </div>
            ) : (
              <div className="w-full max-w-3xl">
                <AnswerCard
                  response={msg.response!}
                  language={language}
                  onOpenCitation={onOpenCitation}
                  onOpenFacilitator={() => onOpenFacilitator(msg.response?.query_text)}
                />
              </div>
            )}
          </div>
        ))}

        {/* Progressive Loading State */}
        {isLoading && (
          <div className="flex flex-col items-start space-y-2 w-full max-w-2xl">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#7FB53D] px-1">
              <Bot className="w-3 h-3 animate-pulse" />
              <span>IP-SAKTI Sahayak</span>
              <span className="text-slate-400 font-normal">• Analyzing</span>
            </div>

            <div className="ayur-card p-4 sm:p-5 rounded-2xl w-full border-l-4 border-l-[#7FB53D] shadow-md space-y-3 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-full bg-[#DEEED9] flex items-center justify-center text-[#7FB53D]">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  </div>
                  <span className="text-xs font-bold text-[#1E2D24]">
                    {t.loadingSteps[loadingStepIndex] || t.loadingSteps[0]}
                  </span>
                </div>
                <span className="text-xs font-mono font-semibold text-[#4B6354] bg-[#DEEED9] px-2 py-0.5 rounded-full">
                  {elapsedSeconds}s
                </span>
              </div>

              {/* Progress Steps Indicators */}
              <div className="grid grid-cols-4 gap-1.5 pt-1">
                {t.loadingSteps.slice(0, 4).map((step, idx) => (
                  <div
                    key={idx}
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      idx < loadingStepIndex
                        ? "bg-[#7FB53D]"
                        : idx === loadingStepIndex
                        ? "bg-[#7FB53D] animate-pulse"
                        : "bg-[#DEEED9]"
                    }`}
                    title={step}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Query Input Box */}
      <div className="sticky bottom-2 z-20 pt-2 bg-gradient-to-t from-[#F3FFFB] via-[#F3FFFB]/90 to-transparent">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery();
          }}
          className="ayur-card p-2 sm:p-2.5 rounded-2xl shadow-lg border border-[#7FB53D]/30 flex items-center gap-2 bg-white"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={t.inputPlaceholder}
            disabled={isLoading}
            className="flex-1 px-3.5 py-2.5 bg-transparent text-sm text-[#1E2D24] placeholder-slate-400 focus:outline-none disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="inline-flex items-center gap-1.5 px-4 sm:px-5 py-2.5 rounded-xl bg-[#7FB53D] hover:bg-[#6EA033] text-white font-bold text-xs sm:text-sm shadow-md shadow-[#7FB53D]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>{t.sendBtn}</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        <p className="text-[10px] text-center text-slate-400 mt-2">
          {language === "hi"
            ? "100% सांविधिक राजपत्र संदर्भों से प्रमाणित • शून्य भ्रम की गारंटी"
            : "100% Statutory Gazette Grounded • Zero Hallucination Guarantee"}
        </p>
      </div>
    </div>
  );
};
