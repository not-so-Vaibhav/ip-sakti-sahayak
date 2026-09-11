"use client";

import React, { useState } from "react";
import { CitationItem } from "@/lib/api";
import { translations } from "@/lib/translations";
import { X, ExternalLink, Copy, Check, BookOpen, Scale, ShieldCheck, Leaf } from "lucide-react";

interface CitationViewerProps {
  citation: CitationItem | null;
  isOpen: boolean;
  onClose: () => void;
  language?: "en" | "hi";
}

export const CitationViewer: React.FC<CitationViewerProps> = ({
  citation,
  isOpen,
  onClose,
  language = "en",
}) => {
  const [copied, setCopied] = useState(false);
  const t = translations[language].sourceViewer;

  if (!isOpen || !citation) return null;

  const handleCopy = () => {
    const textToCopy = `${citation.instrument_name} Section ${citation.section_number || "Unspecified"}\n\n${citation.text_snippet}\n\nOfficial Source: ${citation.source_url}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity">
      <div
        className="w-full max-w-lg bg-[#FAF8F2] h-full shadow-2xl border-l border-[#D8EADB] flex flex-col animate-in slide-in-from-right duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-drawer-title"
      >
        {/* Drawer Header */}
        <div className="p-5 sm:p-6 bg-[#2D5A27] text-white flex items-center justify-between border-b border-[#1E431A]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center text-emerald-200">
              <Leaf className="w-5 h-5 text-[#7FB53D]" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-widest font-extrabold text-emerald-200">
                {t.title}
              </span>
              <h2 id="citation-drawer-title" className="text-base font-extrabold text-white truncate max-w-xs">
                {citation.instrument_name}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-emerald-100 hover:text-white hover:bg-white/10 transition-colors"
            aria-label={t.closeBtn}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="p-5 sm:p-6 flex-1 overflow-y-auto space-y-6 text-[#1E2D24]">
          {/* Section & Authority Badge */}
          <div className="bg-white p-4 sm:p-5 rounded-2xl border border-[#D8EADB] shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-[#4B6354] uppercase tracking-wide">
                {t.section}
              </span>
              <p className="text-lg font-extrabold text-[#2D5A27]">
                Section {citation.section_number || "General Provision"}
              </p>
              {citation.parent_section_label && (
                <p className="text-xs text-[#4B6354] font-medium mt-0.5">
                  {citation.parent_section_label}
                </p>
              )}
            </div>
            <div className="text-right">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/30">
                <ShieldCheck className="w-3.5 h-3.5 text-[#7FB53D]" />
                {citation.authority_level === "primary_law"
                  ? "Primary Statutory Law"
                  : citation.authority_level}
              </span>
            </div>
          </div>

          {/* Exact Statutory Clause (Serif / Legal Styling) */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs uppercase font-extrabold text-[#2D5A27] tracking-wider flex items-center gap-1.5">
                <Scale className="w-3.5 h-3.5 text-[#7FB53D]" />
                {t.clauseTitle}
              </h3>
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2D5A27] hover:text-[#7FB53D] transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy text</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-[#D8EADB] shadow-inner font-serif text-sm leading-relaxed text-[#1E2D24] selection:bg-[#DEEED9]">
              <p className="italic mb-2.5 text-xs text-[#4B6354] font-sans font-bold">
                — Statutory Excerpt from Official Legal Gazette —
              </p>
              &ldquo;{citation.text_snippet}&rdquo;
            </div>
          </div>

          {/* Official Gazette Source Link */}
          <div className="bg-white p-4 sm:p-5 rounded-2xl border border-[#D8EADB] space-y-3">
            <h4 className="text-xs font-bold text-[#4B6354] uppercase tracking-wide">
              {t.officialSource}
            </h4>
            <div className="flex items-center justify-between text-xs gap-2">
              <span className="text-slate-500 truncate max-w-[200px] font-mono text-[11px]">
                {citation.source_url}
              </span>
              <a
                href={citation.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#7FB53D] hover:bg-[#6EA033] text-white font-bold text-xs shadow-xs transition-all hover:scale-105"
              >
                <span>{t.openOfficialLink}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 bg-white border-t border-[#D8EADB] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-[#2D5A27] text-white rounded-xl text-xs font-bold hover:bg-[#1E431A] transition-colors"
          >
            {t.closeBtn}
          </button>
        </div>
      </div>
    </div>
  );
};
