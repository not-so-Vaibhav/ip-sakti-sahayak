"use client";

import React, { useState } from "react";
import { CitationItem, QueryResponse } from "@/lib/api";
import { translations } from "@/lib/translations";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { Copy, Check, BookOpen, ExternalLink, ShieldCheck, Scale, Sparkles } from "lucide-react";

import { MarkdownRenderer } from "./MarkdownRenderer";

interface AnswerCardProps {
  response?: QueryResponse;
  answer?: string;
  citations?: CitationItem[];
  confidenceScore?: number;
  generationAttempts?: number;
  language?: "en" | "hi";
  onOpenCitation: (citation: CitationItem) => void;
  onOpenFacilitator?: () => void;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({
  response,
  answer: directAnswer,
  citations: directCitations,
  confidenceScore: directConfidence,
  generationAttempts: directAttempts,
  language = "en",
  onOpenCitation,
  onOpenFacilitator,
}) => {
  const [copied, setCopied] = useState(false);
  const t = translations[language].chat;

  const answer = response?.answer || directAnswer || "";
  const citations = response?.citations || directCitations || [];
  const confidenceScore = response?.confidence_score ?? directConfidence ?? 0.95;
  const generationAttempts = response?.generation_attempts ?? directAttempts ?? 1;

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="ayur-card p-5 sm:p-7 rounded-3xl space-y-5 transition-all shadow-md">
      {/* Header Bar: Confidence & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3.5 border-b border-[#D8EADB]">
        <div className="flex items-center gap-2.5">
          <ConfidenceMeter score={confidenceScore} language={language} />
          {generationAttempts > 1 && (
            <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/30">
              {t.attemptsBadge}: {generationAttempts}
            </span>
          )}
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-[#2D5A27] bg-[#DEEED9]/60 hover:bg-[#DEEED9] transition-all border border-[#7FB53D]/30 cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700">{t.copiedToast}</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-[#2D5A27]" />
              <span>{t.copyAnswer}</span>
            </>
          )}
        </button>
      </div>

      {/* Answer Body with Rich Markdown & Clickable Footnotes */}
      <div className="text-sm text-[#1E2D24] leading-relaxed font-sans">
        <MarkdownRenderer
          content={answer}
          citations={citations}
          onOpenCitation={onOpenCitation}
        />
      </div>

      {/* Statutory Footnote Citation Pills */}
      {citations.length > 0 && (
        <div className="pt-4 border-t border-[#D8EADB] space-y-3">
          <span className="text-xs font-extrabold uppercase tracking-wider text-[#7FB53D] flex items-center gap-1.5">
            <BookOpen className="w-4 h-4 text-[#7FB53D]" />
            {t.citationsLabel}
          </span>

          <div className="flex flex-wrap gap-2.5">
            {citations.map((c, idx) => (
              <button
                key={c.chunk_id || idx}
                onClick={() => onOpenCitation(c)}
                className="flex items-center gap-2.5 px-3.5 py-2 rounded-2xl text-xs font-semibold bg-[#FAF8F2] text-[#1E2D24] border border-[#D8EADB] hover:border-[#7FB53D] hover:bg-[#DEEED9]/40 transition-all text-left shadow-xs group cursor-pointer"
              >
                <span className="w-5 h-5 rounded-full bg-[#7FB53D] text-white flex items-center justify-center text-[11px] font-extrabold shrink-0">
                  {idx + 1}
                </span>
                <span className="truncate max-w-xs group-hover:text-[#2D5A27]">
                  {c.instrument_name} {c.section_number ? `Sec ${c.section_number}` : ""}
                </span>
                <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-[#7FB53D] shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
