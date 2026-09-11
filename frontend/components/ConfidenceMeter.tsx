"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, Shield } from "lucide-react";

interface ConfidenceMeterProps {
  score: number; // 0.0 to 1.0
  language?: "en" | "hi";
  abstained?: boolean;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  score,
  language = "en",
  abstained = false,
}) => {
  // Normalize score to 5-dot scale
  const percentage = Math.round(score * 100);
  const activeDots = abstained ? 0 : Math.min(5, Math.max(1, Math.round(score * 5)));

  let label = language === "hi" ? "उच्च विश्वसनीयता" : "High Statutory Confidence";
  let colorClass = "text-[#2D5A27]";
  let dotActiveClass = "bg-[#7FB53D]";
  let borderClass = "border-[#7FB53D]/30 bg-[#DEEED9]/60";
  let Icon = ShieldCheck;

  if (abstained || score < 0.45) {
    label = language === "hi" ? "अस्वीकृत / अपर्याप्त" : "Safe Abstention";
    colorClass = "text-amber-800";
    dotActiveClass = "bg-amber-500";
    borderClass = "border-amber-300 bg-amber-50";
    Icon = ShieldAlert;
  } else if (score < 0.65) {
    label = language === "hi" ? "मध्यम विश्वसनीयता" : "Moderate Grounding";
    colorClass = "text-amber-700";
    dotActiveClass = "bg-amber-400";
    borderClass = "border-amber-200 bg-amber-50/50";
    Icon = Shield;
  }

  return (
    <div
      className={`inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full border ${borderClass} text-xs font-bold shadow-xs`}
      aria-label={`Confidence level: ${label} (${percentage}%)`}
    >
      <Icon className={`w-3.5 h-3.5 ${colorClass}`} />
      
      {/* 5-dot visual scale */}
      <div className="flex items-center gap-1" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((dot) => (
          <span
            key={dot}
            className={`w-1.5 h-1.5 rounded-full transition-colors ${
              dot <= activeDots ? dotActiveClass : "bg-[#D8EADB]"
            }`}
          />
        ))}
      </div>

      <span className={`font-bold ${colorClass}`}>
        {label} {!abstained && `(${percentage}%)`}
      </span>
    </div>
  );
};
