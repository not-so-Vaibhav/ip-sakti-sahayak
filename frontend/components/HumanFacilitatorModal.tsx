"use client";

import React, { useState } from "react";
import { translations } from "@/lib/translations";
import { X, UserCheck, Send, CheckCircle2, Leaf } from "lucide-react";

interface HumanFacilitatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  language?: "en" | "hi";
  initialQuery?: string;
  category?: string;
}

export const HumanFacilitatorModal: React.FC<HumanFacilitatorModalProps> = ({
  isOpen,
  onClose,
  language = "en",
  initialQuery = "",
  category = "classical_generic",
}) => {
  const t = translations[language].facilitator;

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [queryContext, setQueryContext] = useState(initialQuery);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  const handleReset = () => {
    setSubmitted(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-150">
      <div
        className="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-[#D8EADB] overflow-hidden flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="facilitator-modal-title"
      >
        {/* Modal Header */}
        <div className="p-5 sm:p-6 bg-[#2D5A27] text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/15 flex items-center justify-center text-emerald-200">
              <UserCheck className="w-5 h-5 text-[#7FB53D]" />
            </div>
            <div>
              <h3 id="facilitator-modal-title" className="text-base sm:text-lg font-extrabold text-white">
                {t.modalTitle}
              </h3>
              <p className="text-xs text-emerald-100/80">{t.modalSubtitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-emerald-100 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 sm:p-8">
          {!submitted ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#1E2D24] uppercase tracking-wide mb-1.5">
                  {t.nameLabel} *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dr. A. Sharma / Ayurvedic Researcher"
                  className="w-full px-4 py-2.5 rounded-2xl border border-[#D8EADB] text-sm text-[#1E2D24] focus:outline-none focus:border-[#7FB53D] focus:ring-2 focus:ring-[#7FB53D]/20 transition-all bg-[#F3FFFB]/40"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-bold text-[#1E2D24] uppercase tracking-wide mb-1.5">
                    {t.emailLabel} *
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="w-full px-4 py-2.5 rounded-2xl border border-[#D8EADB] text-sm text-[#1E2D24] focus:outline-none focus:border-[#7FB53D] focus:ring-2 focus:ring-[#7FB53D]/20 transition-all bg-[#F3FFFB]/40"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#1E2D24] uppercase tracking-wide mb-1.5">
                    {t.phoneLabel}
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full px-4 py-2.5 rounded-2xl border border-[#D8EADB] text-sm text-[#1E2D24] focus:outline-none focus:border-[#7FB53D] focus:ring-2 focus:ring-[#7FB53D]/20 transition-all bg-[#F3FFFB]/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1E2D24] uppercase tracking-wide mb-1.5">
                  {t.queryLabel} *
                </label>
                <textarea
                  rows={3}
                  required
                  value={queryContext}
                  onChange={(e) => setQueryContext(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-2xl border border-[#D8EADB] text-sm text-[#1E2D24] focus:outline-none focus:border-[#7FB53D] focus:ring-2 focus:ring-[#7FB53D]/20 transition-all bg-[#F3FFFB]/40"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-2xl text-xs font-bold text-[#4B6354] hover:bg-[#DEEED9]/50 transition-colors"
                >
                  {t.cancelBtn}
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-2xl text-xs font-bold text-white bg-[#7FB53D] hover:bg-[#6EA033] transition-all shadow-md shadow-[#7FB53D]/25 hover:scale-[1.02]"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{t.submitBtn}</span>
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-6 space-y-4 animate-in zoom-in-95 duration-200">
              <div className="w-14 h-14 rounded-full bg-[#DEEED9] text-[#2D5A27] flex items-center justify-center mx-auto border border-[#7FB53D]/40 shadow-xs">
                <CheckCircle2 className="w-7 h-7 text-[#7FB53D]" />
              </div>
              <div>
                <h4 className="text-lg font-extrabold text-[#1E2D24]">{t.successTitle}</h4>
                <p className="text-xs sm:text-sm text-[#4B6354] max-w-sm mx-auto mt-1 leading-relaxed">
                  {t.successMsg}
                </p>
              </div>
              <button
                onClick={handleReset}
                className="px-6 py-2.5 bg-[#2D5A27] text-white rounded-2xl text-xs font-bold hover:bg-[#1E431A] transition-colors"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
