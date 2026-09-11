"use client";

import React from "react";
import { translations } from "@/lib/translations";
import { Globe, Scale, Sparkles, MessageSquare, Leaf, Home, ArrowRight } from "lucide-react";

interface HeaderProps {
  language: "en" | "hi";
  setLanguage: (lang: "en" | "hi") => void;
  jurisdiction: "india" | "international";
  setJurisdiction: (jur: "india" | "international") => void;
  activeTab: "landing" | "chat" | "classifier" | "comparator";
  setActiveTab: (tab: "landing" | "chat" | "classifier" | "comparator") => void;
  backendOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  setLanguage,
  jurisdiction,
  setJurisdiction,
  activeTab,
  setActiveTab,
  backendOnline,
}) => {
  const t = translations[language];
  const isHi = language === "hi";
  const isLanding = activeTab === "landing";

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#D8EADB] shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          {/* LEFT: Brand Logo & Title */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setActiveTab("landing")}
              className="flex items-center gap-3 text-left group cursor-pointer"
            >
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#7FB53D] to-[#5B8C2A] flex items-center justify-center text-white shadow-md shadow-[#7FB53D]/25 group-hover:scale-105 transition-transform shrink-0">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight group-hover:text-[#7FB53D] transition-colors whitespace-nowrap">
                    {t.appName}
                  </h1>
                  <span className="text-[10px] font-bold px-2 py-0.5 bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/30 rounded-full inline-flex items-center gap-1">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        backendOnline ? "bg-[#7FB53D] animate-pulse" : "bg-amber-400"
                      }`}
                    />
                    v1.0
                  </span>
                </div>
                <p className="text-[11px] text-[#4B6354] font-medium hidden sm:block whitespace-nowrap tracking-wide">
                  {t.appTagline}
                </p>
              </div>
            </button>
          </div>

          {/* CENTER: Navigation Tabs — SHOWN ONLY IN WORKSPACE (Hidden on Landing Page) */}
          {!isLanding ? (
            <nav className="hidden md:flex items-center gap-1 bg-[#F3FFFB] p-1.5 rounded-full border border-[#D8EADB] shadow-2xs animate-in fade-in duration-200">
              <button
                onClick={() => setActiveTab("landing")}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60 transition-all cursor-pointer whitespace-nowrap"
              >
                <Home className="w-3.5 h-3.5 shrink-0" />
                <span>{isHi ? "होम" : "Overview"}</span>
              </button>
              <button
                onClick={() => setActiveTab("chat")}
                className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "chat"
                    ? "bg-[#7FB53D] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.chat}</span>
              </button>
              <button
                onClick={() => setActiveTab("classifier")}
                className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "classifier"
                    ? "bg-[#7FB53D] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.classifier}</span>
              </button>
              <button
                onClick={() => setActiveTab("comparator")}
                className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "comparator"
                    ? "bg-[#7FB53D] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <Scale className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.comparator}</span>
              </button>
            </nav>
          ) : (
            /* On Landing Page: Keep center empty or clean */
            <div className="hidden md:block" />
          )}

          {/* RIGHT CONTROLS */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Show Jurisdiction Switcher ONLY inside workspace */}
            {!isLanding && (
              <div className="flex items-center bg-[#F3FFFB] p-1 rounded-full border border-[#D8EADB] text-xs animate-in fade-in duration-200">
                <button
                  onClick={() => setJurisdiction("india")}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer whitespace-nowrap ${
                    jurisdiction === "india"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                  title={t.jurisdiction.indiaDesc}
                >
                  <span className="w-2 h-2 rounded-full bg-[#7FB53D]" />
                  <span>{isHi ? "भारत" : "India"}</span>
                </button>
                <button
                  onClick={() => setJurisdiction("international")}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer whitespace-nowrap ${
                    jurisdiction === "international"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                  title={t.jurisdiction.internationalDesc}
                >
                  <Globe className="w-3.5 h-3.5" />
                  <span>{isHi ? "विदेश" : "International"}</span>
                </button>
              </div>
            )}

            {/* Language Pill Switcher */}
            <div className="flex items-center bg-[#F3FFFB] p-1 rounded-full border border-[#D8EADB] text-xs">
              <button
                onClick={() => setLanguage("en")}
                className={`px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                  language === "en"
                    ? "bg-[#7FB53D] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24]"
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi")}
                className={`px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                  language === "hi"
                    ? "bg-[#7FB53D] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24]"
                }`}
              >
                हिंदी
              </button>
            </div>

            {/* On Landing Page: Prominent Launch CTA */}
            {isLanding && (
              <button
                onClick={() => setActiveTab("chat")}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#7FB53D] hover:bg-[#6EA033] text-white font-extrabold text-xs sm:text-sm shadow-md shadow-[#7FB53D]/25 transition-all hover:scale-105 cursor-pointer whitespace-nowrap"
              >
                <span>{isHi ? "शुरू करें" : "Launch Assistant"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Mobile Navigation Bar (Shown ONLY inside workspace) */}
        {!isLanding && (
          <div className="md:hidden pb-3 pt-1 flex items-center justify-between gap-1 overflow-x-auto">
            <button
              onClick={() => setActiveTab("landing")}
              className="px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap bg-[#F3FFFB] text-[#4B6354]"
            >
              {isHi ? "होम" : "Overview"}
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap ${
                activeTab === "chat" ? "bg-[#7FB53D] text-white" : "bg-[#F3FFFB] text-[#4B6354]"
              }`}
            >
              {t.nav.chat}
            </button>
            <button
              onClick={() => setActiveTab("classifier")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap ${
                activeTab === "classifier" ? "bg-[#7FB53D] text-white" : "bg-[#F3FFFB] text-[#4B6354]"
              }`}
            >
              {t.nav.classifier}
            </button>
            <button
              onClick={() => setActiveTab("comparator")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap ${
                activeTab === "comparator" ? "bg-[#7FB53D] text-white" : "bg-[#F3FFFB] text-[#4B6354]"
              }`}
            >
              {t.nav.comparator}
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
