"use client";

import React from "react";
import { QueryResponse } from "@/lib/api";
import { translations } from "@/lib/translations";
import { ShieldAlert, UserCheck, RefreshCw, AlertCircle, Sparkles } from "lucide-react";

interface AbstentionCardProps {
  response?: QueryResponse;
  reason?: string | null;
  language?: "en" | "hi";
  onOpenFacilitator?: () => void;
  onEscalate?: () => void;
  onRephrase?: () => void;
}

export const AbstentionCard: React.FC<AbstentionCardProps> = ({
  response,
  reason: directReason,
  language = "en",
  onOpenFacilitator,
  onEscalate,
  onRephrase,
}) => {
  const t = translations[language].abstention;
  const reason = response?.abstention_reason || directReason || null;
  const handleEscalate = onOpenFacilitator || onEscalate || (() => {});

  return (
    <div className="my-3 p-5 sm:p-7 rounded-3xl bg-gradient-to-br from-amber-50/90 via-[#F3FFFB] to-white border-2 border-amber-400/80 shadow-md transition-all">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-2xl bg-amber-100 text-amber-800 shrink-0 mt-0.5 border border-amber-300">
          <ShieldAlert className="w-6 h-6" />
        </div>

        <div className="flex-1 space-y-3.5">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-extrabold text-[#1E2D24]">
                {t.title}
              </h3>
              <span className="text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                Grounding Bar
              </span>
            </div>
            <p className="text-xs sm:text-sm text-[#4B6354] font-medium mt-1">
              {t.subtitle}
            </p>
          </div>

          {/* Explicit Grounding Refusal Reason */}
          {reason && (
            <div className="p-4 rounded-2xl bg-white/95 border border-amber-200 text-xs text-[#1E2D24] space-y-1.5 shadow-xs">
              <span className="font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wide text-[11px]">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                {t.reasonLabel}
              </span>
              <p className="font-mono text-[11px] text-[#4B6354] leading-relaxed">
                {reason}
              </p>
            </div>
          )}

          <p className="text-xs text-[#4B6354] italic">
            {language === "hi"
              ? "यह प्रश्न किसी योग्य आयुष कानूनी विशेषज्ञ की समीक्षा की मांग करता है — गलत अनुमान लगाने से इनकार करना बेहतर है।"
              : "This question requires verified statutory grounding — our system safely abstains rather than speculating on non-existent provisions."}
          </p>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              onClick={handleEscalate}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl text-xs font-bold text-white bg-[#7FB53D] hover:bg-[#6EA033] transition-all shadow-md shadow-[#7FB53D]/25 hover:scale-[1.02]"
            >
              <UserCheck className="w-4 h-4 text-white" />
              <span>{t.talkToFacilitator}</span>
            </button>
            {onRephrase && (
              <button
                onClick={onRephrase}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-2xl text-xs font-bold text-[#2D5A27] bg-[#DEEED9] hover:bg-[#d0e5cb] border border-[#7FB53D]/30 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>{t.rephraseBtn}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
