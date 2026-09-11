"use client";

import React, { useState, useEffect } from "react";
import { api, DecisionQuestion, CategoryOutcome, FormulationCategory } from "@/lib/api";
import { translations } from "@/lib/translations";
import { Sparkles, HelpCircle, ArrowRight, RotateCcw, ShieldCheck, CheckCircle2, AlertCircle, Leaf } from "lucide-react";

interface ClassificationWizardProps {
  language: "en" | "hi";
  onCategorySelected: (category: FormulationCategory) => void;
  onNavigateToChat: () => void;
}

export const ClassificationWizard: React.FC<ClassificationWizardProps> = ({
  language,
  onCategorySelected,
  onNavigateToChat,
}) => {
  const t = translations[language].classifier;
  const isHi = language === "hi";

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<DecisionQuestion | null>(null);
  const [completed, setCompleted] = useState<boolean>(false);
  const [categoryOutcome, setCategoryOutcome] = useState<CategoryOutcome | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [stepIndex, setStepIndex] = useState<number>(1);
  const [history, setHistory] = useState<{ questionId: string; optionId: string }[]>([]);

  // Start fresh classification flow
  const initWizard = async () => {
    setLoading(true);
    setError(null);
    setCompleted(false);
    setCategoryOutcome(null);
    setStepIndex(1);
    setHistory([]);

    try {
      const res = await api.startClassification(language);
      setSessionId(res.session_id);
      setCurrentQuestion(res.question);
      if (res.completed && res.category) {
        setCompleted(true);
        setCategoryOutcome(res.category);
        onCategorySelected(res.category.category_id);
      }
    } catch (err: any) {
      console.error("Error starting classification:", err);
      setError(err.message || "Could not load classification wizard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initWizard();
  }, [language]);

  const handleSelectOption = async (optionId: string) => {
    if (!sessionId || !currentQuestion) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.nextClassificationStep(
        sessionId,
        currentQuestion.id,
        optionId,
        language
      );

      setHistory((prev) => [...prev, { questionId: currentQuestion.id, optionId }]);
      setStepIndex((prev) => prev + 1);

      if (res.completed && res.category) {
        setCompleted(true);
        setCategoryOutcome(res.category);
        setCurrentQuestion(null);
        onCategorySelected(res.category.category_id);
      } else if (res.question) {
        setCurrentQuestion(res.question);
      }
    } catch (err: any) {
      console.error("Error advancing classification:", err);
      setError(err.message || "Failed to process option.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-6 sm:py-8 px-4 sm:px-6">
      {/* Wizard Header */}
      <div className="text-center space-y-2 mb-8">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#DEEED9] text-[#2D5A27] text-xs font-bold border border-[#7FB53D]/30 shadow-xs">
          <Leaf className="w-3.5 h-3.5 text-[#7FB53D]" />
          <span>{t.title}</span>
        </div>
        <h2 className="text-2xl sm:text-4xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight">
          {completed ? t.completedBadge : `${t.step} ${stepIndex} ${t.of} 4`}
        </h2>
        <p className="text-xs sm:text-sm text-[#4B6354] max-w-xl mx-auto font-normal">
          {t.subtitle}
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-300 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={initWizard}
            className="text-xs font-bold underline hover:text-amber-950"
          >
            Retry
          </button>
        </div>
      )}

      {/* QUESTION CARD (Step by Step) */}
      {!completed && currentQuestion && (
        <div className="ayur-card ayur-arch-lg p-6 sm:p-9 space-y-6 animate-in fade-in duration-200 shadow-lg">
          {/* Step Progress Dots */}
          <div className="flex items-center justify-between text-xs text-[#4B6354] font-bold border-b border-[#D8EADB] pb-4">
            <span className="text-[#2D5A27] font-bold">
              {t.step} {stepIndex}
            </span>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4].map((step) => (
                <span
                  key={step}
                  className={`w-3 h-3 rounded-full transition-all ${
                    step === stepIndex
                      ? "bg-[#7FB53D] ring-4 ring-[#DEEED9] scale-110"
                      : step < stepIndex
                      ? "bg-[#2D5A27]"
                      : "bg-[#D8EADB]"
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Question Prompt */}
          <div className="space-y-2">
            <h3 className="text-lg sm:text-xl font-bold text-[#1E2D24] leading-snug">
              {currentQuestion.text}
            </h3>
            {currentQuestion.subtext && (
              <p className="text-xs sm:text-sm text-[#4B6354] font-normal leading-relaxed">
                {currentQuestion.subtext}
              </p>
            )}
          </div>

          {/* Regulatory Rationale Box ("Why we're asking this") */}
          {currentQuestion.rationale && (
            <div className="p-4 sm:p-5 rounded-2xl bg-[#FAF8F2] border border-[#D8EADB] text-xs text-[#1E2D24] flex items-start gap-3">
              <HelpCircle className="w-4 h-4 text-[#7FB53D] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-[#2D5A27] block mb-0.5 uppercase tracking-wide text-[11px]">
                  {t.whyAsking}
                </span>
                <p className="leading-relaxed text-[#4B6354]">
                  {currentQuestion.rationale}
                </p>
              </div>
            </div>
          )}

          {/* Decision Options */}
          <div className="grid grid-cols-1 gap-3.5 pt-2">
            {currentQuestion.options.map((option) => (
              <button
                key={option.id}
                onClick={() => handleSelectOption(option.id)}
                disabled={loading}
                className="w-full text-left p-4 sm:p-5 rounded-2xl border border-[#D8EADB] bg-white hover:bg-[#DEEED9]/40 hover:border-[#7FB53D] transition-all group flex items-center justify-between cursor-pointer disabled:opacity-50 shadow-xs hover:shadow-md"
              >
                <div>
                  <span className="text-sm font-bold text-[#1E2D24] group-hover:text-[#2D5A27] block">
                    {option.label}
                  </span>
                  {option.description && (
                    <span className="text-xs text-[#4B6354] group-hover:text-slate-700 mt-1 block">
                      {option.description}
                    </span>
                  )}
                </div>
                <div className="w-8 h-8 rounded-full bg-[#F3FFFB] group-hover:bg-[#7FB53D] flex items-center justify-center text-slate-400 group-hover:text-white transition-colors shrink-0 ml-4">
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* OUTCOME CARD (Clean, Professional, Non-Celebratory) */}
      {completed && categoryOutcome && (
        <div className="ayur-card ayur-arch-lg border-2 border-[#7FB53D]/40 shadow-xl p-6 sm:p-9 space-y-6 animate-in zoom-in-95 duration-200">
          <div className="flex items-center gap-3.5 border-b border-[#D8EADB] pb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center border border-[#7FB53D]/30 shadow-xs">
              <ShieldCheck className="w-7 h-7 text-[#7FB53D]" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#7FB53D]">
                {t.outcomeTitle}
              </span>
              <h3 className="text-xl sm:text-2xl font-extrabold text-[#1E2D24]">
                {categoryOutcome.name}
              </h3>
            </div>
          </div>

          <p className="text-sm text-[#4B6354] leading-relaxed font-normal">
            {categoryOutcome.description}
          </p>

          {/* Statutory Implications Box */}
          <div className="p-5 sm:p-6 rounded-2xl bg-[#FAF8F2] border border-[#D8EADB] space-y-3.5">
            <h4 className="text-xs uppercase font-extrabold tracking-wider text-[#2D5A27] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#7FB53D]" />
              {t.whatThisMeans}
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm text-[#1E2D24]">
              {categoryOutcome.key_implications.map((imp, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="text-[#7FB53D] font-bold text-sm shrink-0">•</span>
                  <span className="leading-relaxed">{imp}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3.5 pt-4 border-t border-[#D8EADB]">
            <button
              onClick={initWizard}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-5 py-3 rounded-2xl text-xs font-bold text-[#4B6354] bg-[#DEEED9]/60 hover:bg-[#DEEED9] transition-colors border border-[#7FB53D]/30"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#2D5A27]" />
              <span>{t.redoBtn}</span>
            </button>

            <button
              onClick={onNavigateToChat}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3 rounded-2xl text-sm font-bold text-white bg-[#7FB53D] hover:bg-[#6EA033] transition-all shadow-md shadow-[#7FB53D]/25 hover:scale-[1.02]"
            >
              <span>{t.askQuestionBtn}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
