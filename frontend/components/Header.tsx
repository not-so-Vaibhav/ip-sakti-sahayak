"use client";

import React, { useState } from "react";
import { translations } from "@/lib/translations";
import {
  Globe,
  Scale,
  Sparkles,
  MessageSquare,
  Leaf,
  Home,
  ArrowRight,
  Search,
  Menu,
  X,
  ShieldCheck,
} from "lucide-react";

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const t = translations[language];
  const isHi = language === "hi";
  const isLanding = activeTab === "landing";

  const handleNavClick = (tab: "landing" | "chat" | "classifier" | "comparator" | "investigate") => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#D8EADB] shadow-xs print:hidden w-full">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18 gap-2 sm:gap-4">
          {/* LEFT: Brand Logo & Title */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <button
              onClick={() => handleNavClick("landing")}
              className="flex items-center gap-2 sm:gap-3 text-left group cursor-pointer"
            >
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-[#7FB53D] to-[#2D5A27] flex items-center justify-center text-white shadow-md shadow-[#7FB53D]/25 group-hover:scale-105 transition-transform shrink-0">
                <Leaf className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <h1 className="text-base sm:text-xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight group-hover:text-[#2D5A27] transition-colors whitespace-nowrap">
                    {t.appName}
                  </h1>
                  <span className="text-[9px] sm:text-[10px] font-bold px-1.5 sm:px-2 py-0.5 bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/30 rounded-full inline-flex items-center gap-1">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        backendOnline ? "bg-[#7FB53D] animate-pulse" : "bg-amber-400"
                      }`}
                    />
                    v1.0
                  </span>
                </div>
                <p className="text-[10px] sm:text-[11px] text-[#4B6354] font-medium hidden md:block whitespace-nowrap tracking-wide">
                  {t.appTagline}
                </p>
              </div>
            </button>
          </div>

          {/* CENTER: Desktop Navigation Tabs (Hidden on Mobile & on Landing Page) */}
          {!isLanding ? (
            <nav className="hidden lg:flex items-center gap-1 bg-[#F4F9F2] p-1 rounded-full border border-[#D8EADB] shadow-2xs animate-in fade-in duration-200">
              <button
                onClick={() => handleNavClick("landing")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-[#4B6354] hover:text-[#1E2D24] hover:bg-[#DEEED9]/60 transition-all cursor-pointer whitespace-nowrap"
              >
                <Home className="w-3.5 h-3.5 shrink-0" />
                <span>{isHi ? "होम" : "Overview"}</span>
              </button>
              <button
                onClick={() => handleNavClick("chat")}
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
                onClick={() => handleNavClick("classifier")}
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
                onClick={() => handleNavClick("comparator")}
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
                onClick={() => handleNavClick("investigate")}
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
            <div className="hidden lg:block" />
          )}

          {/* RIGHT CONTROLS */}
          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            {/* Desktop Jurisdiction Switcher (Hidden on Mobile) */}
            {!isLanding && (
              <div className="hidden sm:flex items-center bg-[#F4F9F2] p-1 rounded-full border border-[#D8EADB] text-xs animate-in fade-in duration-200">
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
            <div className="flex items-center bg-[#F4F9F2] p-0.5 sm:p-1 rounded-full border border-[#D8EADB] text-xs shrink-0">
              <button
                onClick={() => setLanguage("en")}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full font-bold transition-all cursor-pointer text-[10px] sm:text-xs ${
                  language === "en"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24]"
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi")}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full font-bold transition-all cursor-pointer text-[10px] sm:text-xs ${
                  language === "hi"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#4B6354] hover:text-[#1E2D24]"
                }`}
              >
                हिंदी
              </button>
            </div>

            {/* Desktop Launch CTA */}
            {isLanding && (
              <button
                onClick={() => handleNavClick("chat")}
                className="hidden sm:inline-flex items-center gap-1.5 sm:gap-2 px-4 sm:px-5 py-1.5 sm:py-2 rounded-full bg-[#2D5A27] hover:bg-[#3D7A35] text-white font-bold text-xs sm:text-sm shadow-md shadow-[#2D5A27]/20 transition-all hover:scale-105 cursor-pointer whitespace-nowrap"
              >
                <span>{isHi ? "शुरू करें" : "Launch Assistant"}</span>
                <ArrowRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </button>
            )}

            {/* MOBILE HAMBURGER BUTTON */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl bg-[#F4F9F2] hover:bg-[#DEEED9] text-[#2D5A27] border border-[#D8EADB] transition-all cursor-pointer flex items-center justify-center shrink-0"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* MOBILE SLIDE-DOWN HAMBURGER MENU */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-[#D8EADB] bg-white/98 backdrop-blur-xl py-4 px-2 space-y-4 animate-in slide-in-from-top-2 duration-200 shadow-xl rounded-b-2xl">
            {/* Navigation Links */}
            <div className="space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#7FB53D] px-3 block mb-1">
                {isHi ? "नेविगेशन" : "Navigation"}
              </span>

              <button
                onClick={() => handleNavClick("landing")}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${
                  activeTab === "landing"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#1E2D24] hover:bg-[#DEEED9]/50"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Home className="w-4 h-4" />
                  <span>{isHi ? "होम (परिचय)" : "Overview (Home)"}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 opacity-60" />
              </button>

              <button
                onClick={() => handleNavClick("chat")}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${
                  activeTab === "chat"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#1E2D24] hover:bg-[#DEEED9]/50"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <MessageSquare className="w-4 h-4" />
                  <span>{t.nav.chat}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 opacity-60" />
              </button>

              <button
                onClick={() => handleNavClick("classifier")}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${
                  activeTab === "classifier"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#1E2D24] hover:bg-[#DEEED9]/50"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4" />
                  <span>{t.nav.classifier}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 opacity-60" />
              </button>

              <button
                onClick={() => handleNavClick("comparator")}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${
                  activeTab === "comparator"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#1E2D24] hover:bg-[#DEEED9]/50"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Scale className="w-4 h-4" />
                  <span>{t.nav.comparator}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 opacity-60" />
              </button>

              <button
                onClick={() => handleNavClick("investigate")}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${
                  activeTab === "investigate"
                    ? "bg-[#2D5A27] text-white shadow-xs"
                    : "text-[#1E2D24] hover:bg-[#DEEED9]/50"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Search className="w-4 h-4" />
                  <span>{isHi ? "IP जांच इंजन" : "IP Investigation"}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 opacity-60" />
              </button>
            </div>

            {/* Mobile Jurisdiction Selector */}
            <div className="pt-2 border-t border-[#D8EADB] px-2 space-y-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#7FB53D] block">
                {isHi ? "क्षेत्राधिकार (Jurisdiction)" : "Jurisdiction Regime"}
              </span>
              <div className="grid grid-cols-2 gap-2 bg-[#F4F9F2] p-1 rounded-xl border border-[#D8EADB]">
                <button
                  onClick={() => setJurisdiction("india")}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    jurisdiction === "india"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7FB53D]" />
                  <span>{isHi ? "भारत" : "India (IN)"}</span>
                </button>
                <button
                  onClick={() => setJurisdiction("international")}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    jurisdiction === "international"
                      ? "bg-[#2D5A27] text-white shadow-xs"
                      : "text-[#4B6354] hover:text-[#1E2D24]"
                  }`}
                >
                  <Globe className="w-3 h-3" />
                  <span>{isHi ? "विदेश" : "Global"}</span>
                </button>
              </div>
            </div>

            {/* Quick Action Button */}
            {isLanding && (
              <div className="pt-2 px-2">
                <button
                  onClick={() => handleNavClick("chat")}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#2D5A27] text-white font-bold text-sm shadow-md shadow-[#2D5A27]/20"
                >
                  <span>{isHi ? "सांविधिक सहायक शुरू करें" : "Launch Assistant"}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
