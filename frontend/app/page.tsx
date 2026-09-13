"use client";

import React, { useState, useEffect } from "react";
import { api, CitationItem, FormulationCategory } from "@/lib/api";
import { Header } from "@/components/Header";
import { LandingHero } from "@/components/LandingHero";
import { ClassificationWizard } from "@/components/ClassificationWizard";
import { ChatInterface } from "@/components/ChatInterface";
import { RegimeComparator } from "@/components/RegimeComparator";
import { CitationViewer } from "@/components/CitationViewer";
import { HumanFacilitatorModal } from "@/components/HumanFacilitatorModal";
import { InvestigationDashboard } from "@/components/InvestigationDashboard";
import { Leaf } from "lucide-react";

export default function Home() {
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [jurisdiction, setJurisdiction] = useState<"india" | "international">("india");
  const [activeTab, setActiveTab] = useState<"landing" | "chat" | "classifier" | "comparator" | "investigate">("landing");
  const [activeCategory, setActiveCategory] = useState<FormulationCategory>("classical_generic");
  const [initialChatQuery, setInitialChatQuery] = useState<string | undefined>(undefined);
  
  // Modals & Drawers
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);
  const [isCitationOpen, setIsCitationOpen] = useState(false);
  const [isFacilitatorOpen, setIsFacilitatorOpen] = useState(false);
  const [facilitatorQuery, setFacilitatorQuery] = useState("");
  const [backendOnline, setBackendOnline] = useState(true);

  // Check backend health on mount
  useEffect(() => {
    const checkStatus = async () => {
      const health = await api.checkHealth();
      setBackendOnline(health.status === "healthy" || health.status === "ok");
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenCitation = (citation: CitationItem) => {
    setSelectedCitation(citation);
    setIsCitationOpen(true);
  };

  const handleOpenFacilitator = (queryText?: string) => {
    setFacilitatorQuery(queryText || "");
    setIsFacilitatorOpen(true);
  };

  const handleCategoryClassified = (cat: FormulationCategory) => {
    setActiveCategory(cat);
  };

  const handleNavigateToTab = (
    tab: "chat" | "classifier" | "comparator" | "investigate",
    query?: string,
    category?: FormulationCategory
  ) => {
    if (category) {
      setActiveCategory(category);
    }
    if (query) {
      setInitialChatQuery(query);
    }
    setActiveTab(tab);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F6FAF5] text-[#1E2D24] selection:bg-[#DEEED9] selection:text-[#2D5A27] font-sans">
      {/* App Header & Navigation */}
      <Header
        language={language}
        setLanguage={setLanguage}
        jurisdiction={jurisdiction}
        setJurisdiction={setJurisdiction}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendOnline={backendOnline}
      />

      {/* Main Tab Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-6 lg:p-8 print:p-0 print:max-w-none flex flex-col min-w-0 max-w-full overflow-x-hidden">
        {activeTab === "landing" && (
          <LandingHero
            language={language}
            onNavigateToTab={handleNavigateToTab}
          />
        )}

        {activeTab === "chat" && (
          <ChatInterface
            language={language}
            jurisdiction={jurisdiction}
            activeCategory={activeCategory}
            onSelectCategory={setActiveCategory}
            onOpenCitation={handleOpenCitation}
            onOpenFacilitator={handleOpenFacilitator}
            initialQuery={initialChatQuery}
          />
        )}

        {activeTab === "classifier" && (
          <ClassificationWizard
            language={language}
            onCategorySelected={handleCategoryClassified}
            onNavigateToChat={() => setActiveTab("chat")}
          />
        )}

        {activeTab === "comparator" && (
          <RegimeComparator language={language} />
        )}

        {activeTab === "investigate" && (
          <InvestigationDashboard
            language={language}
            jurisdiction={jurisdiction}
            activeCategory={activeCategory}
            onOpenCitation={handleOpenCitation}
            onOpenFacilitator={handleOpenFacilitator}
          />
        )}
      </main>

      {/* Slide-out Statutory Source Viewer Drawer */}
      <CitationViewer
        citation={selectedCitation}
        isOpen={isCitationOpen}
        onClose={() => setIsCitationOpen(false)}
        language={language}
      />

      {/* Human Facilitator Escalation Modal */}
      <HumanFacilitatorModal
        isOpen={isFacilitatorOpen}
        onClose={() => setIsFacilitatorOpen(false)}
        language={language}
        initialQuery={facilitatorQuery}
        category={activeCategory}
      />

      {/* Standing Footer with Legal Disclaimer */}
      <footer className="bg-white/80 border-t border-[#D8EADB] py-8 px-4 text-center text-xs text-[#4B6354] space-y-3 print:hidden">
        <div className="max-w-4xl mx-auto flex flex-wrap items-center justify-center gap-3 font-semibold text-[#2D5A27]">
          <div className="flex items-center gap-1.5">
            <Leaf className="w-3.5 h-3.5 text-[#7FB53D]" />
            <span>IP-SAKTI Sahayak</span>
          </div>
          <span>•</span>
          <span>Patents Act, 1970</span>
          <span>•</span>
          <span>Biological Diversity Act, 2002</span>
          <span>•</span>
          <span>Drugs & Cosmetics Act, 1940</span>
          <span>•</span>
          <span>FSSAI Ayurveda Aahar 2022</span>
        </div>
        <p className="max-w-2xl mx-auto text-slate-500 text-[11px] leading-relaxed">
          {language === "hi"
            ? "यह उपकरण केवल सांविधिक एवं नियामक संदर्भ प्रदान करने के लिए है। किसी भी पेटेंट आवेदन या व्यावसायिक निर्णय से पहले पंजीकृत पेटेंट एजेंट या कानूनी विशेषज्ञ से परामर्श लें।"
            : "This AI tool provides citation-grounded statutory information for educational and preliminary screening purposes only. Consult a registered patent agent or legal practitioner for formal filings."}
        </p>
      </footer>
    </div>
  );
}
