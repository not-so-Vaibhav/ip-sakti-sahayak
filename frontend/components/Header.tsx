"use client";

import React from "react";
import { translations } from "@/lib/translations";
import { Globe, Scale, Sparkles, MessageSquare, Leaf, Home, ArrowRight, Search } from "lucide-react";

interface HeaderProps {
  language: "en" | "hi";
  setLanguage: (lang: "en" | "hi") => void;
  jurisdiction: "india" | "international";
  setJurisdiction: (jur: "india" | "international") => void;
  activeTab: "landing" | "chat" | "classifier" | "comparator" | "investigate";
  setActiveTab: (tab: "landing" | "chat" | "classifier" | "comparator" | "investigate") => void;
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
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#D8EADB] shadow-xs print:hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18 gap-3 sm:gap-4">
          {/* LEFT: Brand Logo & Title */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setActiveTab("landing")}
              className="flex items-center gap-2.5 sm:gap-3 text-left group cursor-pointer"
            >
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-[#7FB53D] to-[#2D5A27] flex items-center justify-center text-white shadow-md shadow-[#7FB53D]/25 group-hover:scale-105 transition-transform shrink-0">
                <Leaf className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <h1 className="text-lg sm:text-xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight group-hover:text-[#2D5A27] transition-colors whitespace-nowrap">
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
                <p className="text-[10px] sm:text-[11px] text-[#4B6354] font-medium hidden sm:block whitespace-nowrap tracking-wide">
                  {t.appTagline}
                </p>
              </div>
            </button>
          </div>

          {/* CENTER: Navigation Tabs — SHOWN ONLY IN WORKSPACE (Hidden on Landing Page) */}
          {!isLanding ? (
            <nav className="hidden lg:flex items-center gap-1 bg-[#F4F9F2] p-1 rounded-full border border-[#D8EADB] shadow-2xs animate-in fade-in duration-200">
              <button
                onClick={() => setActiveTab("landing")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60 transition-all cursor-pointer whitespace-nowrap"
              >
                <Home className="w-3.5 h-3.5 shrink-0" />
                <span>{isHi ? "होम" : "Overview"}</span>
              </button>
              <button
                onClick={() => setActiveTab("chat")}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "chat"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.chat}</span>
              </button>
              <button
                onClick={() => setActiveTab("classifier")}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "classifier"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.classifier}</span>
              </button>
              <button
                onClick={() => setActiveTab("comparator")}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "comparator"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <Scale className="w-3.5 h-3.5 shrink-0" />
                <span>{t.nav.comparator}</span>
              </button>
              <button
                onClick={() => setActiveTab("investigate")}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === "investigate"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60"
                }`}
              >
                <Search className="w-3.5 h-3.5 shrink-0" />
                <span>{isHi ? "IP जांच" : "IP Investigation"}</span>
              </button>
            </nav>
          ) : (
            /* On Landing Page: Keep center empty or clean */
            <div className="hidden lg:block" />
          )}

          {/* RIGHT CONTROLS */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* Show Jurisdiction Switcher ONLY inside workspace */}
            {!isLanding && (
              <div className="flex items-center bg-[#F4F9F2] p-1 rounded-full border border-[#D8EADB] text-xs animate-in fade-in duration-200">
                <button
                  onClick={() => setJurisdiction("india")}
                  className={`inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer whitespace-nowrap text-[11px] sm:text-xs ${
                    jurisdiction === "india"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                  title={t.jurisdiction.indiaDesc}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7FB53D]" />
                  <span>{isHi ? "भारत" : "India"}</span>
                </button>
                <button
                  onClick={() => setJurisdiction("international")}
                  className={`inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer whitespace-nowrap text-[11px] sm:text-xs ${
                    jurisdiction === "international"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                  title={t.jurisdiction.internationalDesc}
                >
                  <Globe className="w-3 h-3" />
                  <span>{isHi ? "विदेश" : "Global"}</span>
                </button>
              </div>
            )}

            {/* Language Pill Switcher */}
            <div className="flex items-center bg-[#F4F9F2] p-1 rounded-full border border-[#D8EADB] text-xs shrink-0">
              <button
                onClick={() => setLanguage("en")}
                className={`px-2.5 sm:px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer text-[11px] sm:text-xs ${
                  language === "en"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24]"
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi")}
                className={`px-2.5 sm:px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer text-[11px] sm:text-xs ${
                  language === "hi"
                    ? "bg-[#2D5A27] text-white shadow-xs"
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
                className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-[#2D5A27] hover:bg-[#3D7A35] text-white font-bold text-xs sm:text-sm shadow-md shadow-[#2D5A27]/20 transition-all hover:scale-105 cursor-pointer whitespace-nowrap"
              >
                <span>{isHi ? "शुरू करें" : "Launch Assistant"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Mobile & Tablet Navigation Bar (Shown inside workspace on screens below lg) */}
        {!isLanding && (
          <div className="lg:hidden pb-3 pt-1 flex items-center justify-start gap-1.5 overflow-x-auto no-scrollbar">
            <button
              onClick={() => setActiveTab("landing")}
              className="px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap bg-[#F3FFFB] text-[#4B6354] border border-[#D8EADB]/60 flex items-center gap-1"
            >
              <Home className="w-3 h-3" />
              <span>{isHi ? "होम" : "Overview"}</span>
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap flex items-center gap-1 ${
                activeTab === "chat" ? "bg-[#2D5A27] text-white" : "bg-[#F3FFFB] text-[#4B6354] border border-[#D8EADB]/60"
              }`}
            >
              <MessageSquare className="w-3 h-3" />
              <span>{t.nav.chat}</span>
            </button>
            <button
              onClick={() => setActiveTab("classifier")}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap flex items-center gap-1 ${
                activeTab === "classifier" ? "bg-[#2D5A27] text-white" : "bg-[#F3FFFB] text-[#4B6354] border border-[#D8EADB]/60"
              }`}
            >
              <Sparkles className="w-3 h-3" />
              <span>{t.nav.classifier}</span>
            </button>
            <button
              onClick={() => setActiveTab("comparator")}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap flex items-center gap-1 ${
                activeTab === "comparator" ? "bg-[#2D5A27] text-white" : "bg-[#F3FFFB] text-[#4B6354] border border-[#D8EADB]/60"
              }`}
            >
              <Scale className="w-3 h-3" />
              <span>{t.nav.comparator}</span>
            </button>
            <button
              onClick={() => setActiveTab("investigate")}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap flex items-center gap-1 ${
                activeTab === "investigate" ? "bg-[#2D5A27] text-white" : "bg-[#F3FFFB] text-[#4B6354] border border-[#D8EADB]/60"
              }`}
            >
              <Search className="w-3 h-3" />
              <span>{isHi ? "IP जांच" : "IP Investigation"}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
