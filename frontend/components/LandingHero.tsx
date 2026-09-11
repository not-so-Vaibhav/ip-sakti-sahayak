"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  Sparkles,
  MessageSquare,
  Scale,
  ShieldCheck,
  ArrowRight,
  BookOpen,
  Leaf,
  CheckCircle2,
  Globe,
  ChevronRight,
  Send,
  HelpCircle,
} from "lucide-react";
import { FormulationCategory } from "@/lib/api";

interface LandingHeroProps {
  language: "en" | "hi";
  onNavigateToTab: (
    tab: "chat" | "classifier" | "comparator" | "investigate",
    initialQuery?: string,
    category?: FormulationCategory
  ) => void;
}

/* Realistic Botanical Leaf SVG Component */
const BotanicalLeaf: React.FC<{
  className?: string;
  size?: number;
  rotation?: number;
  flip?: boolean;
}> = ({ className = "", size = 32, rotation = 0, flip = false }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 100 100"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`leaf-shadow pointer-events-none select-none transition-transform ${className}`}
    style={{
      transform: `rotate(${rotation}deg) ${flip ? "scaleX(-1)" : ""}`,
    }}
  >
    <defs>
      <linearGradient id="leafGrad1" x1="10%" y1="10%" x2="90%" y2="90%">
        <stop offset="0%" stopColor="#9AD153" />
        <stop offset="50%" stopColor="#7FB53D" />
        <stop offset="100%" stopColor="#3E6F20" />
      </linearGradient>
      <linearGradient id="leafGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#6EA033" />
        <stop offset="100%" stopColor="#244B1C" />
      </linearGradient>
    </defs>
    {/* Realistic Leaf Blade */}
    <path
      d="M15 85 C 10 50, 40 15, 85 10 C 90 45, 60 80, 15 85 Z"
      fill="url(#leafGrad1)"
    />
    {/* Leaf Central Vein */}
    <path
      d="M15 85 Q 45 50 85 10"
      stroke="url(#leafGrad2)"
      strokeWidth="2.5"
      strokeLinecap="round"
      opacity="0.8"
    />
    {/* Lateral Veins */}
    <path
      d="M32 68 Q 38 58 48 64 M45 53 Q 54 44 65 50 M60 38 Q 68 30 78 35"
      stroke="#DEEED9"
      strokeWidth="1.2"
      strokeLinecap="round"
      opacity="0.6"
    />
    {/* Natural Highlight */}
    <path
      d="M25 75 C 30 50, 50 25, 75 18 C 55 35, 35 55, 25 75 Z"
      fill="#FFFFFF"
      opacity="0.18"
    />
  </svg>
);

export const LandingHero: React.FC<LandingHeroProps> = ({
  language,
  onNavigateToTab,
}) => {
  const isHi = language === "hi";
  const [quickQuery, setQuickQuery] = useState("");

  const handleQuickSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickQuery.trim()) {
      onNavigateToTab("chat", quickQuery.trim());
    } else {
      onNavigateToTab("chat");
    }
  };

  /* 4 Botanical Treatment & Formulation Modules */
  const treatments = [
    {
      id: "amla_tulsi",
      image: "/images/amla_tulsi.jpg",
      title: isHi ? "आमलकी एवं तुलसी लेप" : "Amla & Tulasi Lepa",
      categoryBadge: isHi ? "शास्त्रीय जेनेरिक" : "Classical Generic",
      category: "classical_generic" as FormulationCategory,
      statute: isHi ? "धारा 3(p) पारंपरिक ज्ञान बार" : "Section 3(p) TKDL Clearance",
      description: isHi
        ? "चरक व सुश्रुत संहिता में वर्णित पारंपरिक फॉर्मूलेशन। सार्वजनिक ज्ञान होने के कारण पेटेंट वर्जित, परंतु $0 वैधानिक शुल्क के साथ विनिर्माण अनुमेय।"
        : "A classical herbal combination of Amalaki and Tulsi described in First Schedule texts. Protected against unauthorized patenting under Section 3(p).",
      query: isHi
        ? "क्या चरक संहिता के शास्त्रीय नुस्खे पर धारा 3(p) के तहत भारत में पेटेंट मिल सकता है?"
        : "Can I obtain a product patent in India for an unmodified classical turmeric and neem wound formulation described in Charaka Samhita?",
    },
    {
      id: "turmeric_lepa",
      image: "/images/turmeric_lepa.jpg",
      title: isHi ? "कस्तूरी मंजल लेप" : "Kasturi Manjal Lepa",
      categoryBadge: isHi ? "फाइटोफार्मास्युटिकल" : "Phytopharmaceutical",
      category: "phytopharmaceutical" as FormulationCategory,
      statute: isHi ? "नियम 122E न्यूनतम 4-मार्कर" : "Rule 122E 4-Bioactive Standard",
      description: isHi
        ? "मानकीकृत करक्यूमिन व आवश्यक तेल अंश। CDSCO नियम 122E के तहत कम से कम 4 बायोएक्टिव मार्करों और IND सुरक्षा परीक्षण की अनिवार्यता।"
        : "An effective standardized botanical fraction requiring minimum 4-marker chromatographic fingerprinting and Phase I-III IND validation.",
      query: isHi
        ? "नियम 122E के तहत फाइटोफार्मास्युटिकल दवा के लिए न्यूनतम बायोएक्टिव मार्कर आवश्यकताएं क्या हैं?"
        : "What are the minimum bioactive marker requirements and regulatory standards for a phytopharmaceutical drug under Rule 122E?",
    },
    {
      id: "neem_serum",
      image: "/images/neem_serum.jpg",
      title: isHi ? "नीम एवं तुलसी सीरम" : "Neem & Tulsi Purifying Serum",
      categoryBadge: isHi ? "जैव विविधता ABS" : "Biological Diversity ABS",
      category: "patent_or_proprietary" as FormulationCategory,
      statute: isHi ? "NBA धारा 6 पूर्व अनुमति" : "NBA Section 6 Prior Approval",
      description: isHi
        ? "भारतीय जैविक संसाधनों पर आधारित नवीन फॉर्मूलेशन। विदेशी संस्थाओं या विदेशी पेटेंट फाइलिंग हेतु राष्ट्रीय जैव विविधता प्राधिकरण से पूर्व अनुमति अनिवार्य।"
        : "Proprietary botanical formulations using Indian bio-resources require mandatory NBA Form III clearance prior to commercial patent grant.",
      query: isHi
        ? "क्या किसी विदेशी कंपनी को भारतीय जैविक संसाधनों पर आधारित पेटेंट दाखिल करने से पहले NBA से अनुमति लेनी होगी?"
        : "Does a foreign company need prior approval from the National Biodiversity Authority before filing a patent based on Indian biological resources?",
    },
    {
      id: "ginger_lahyam",
      image: "/images/ginger_lahyam.jpg",
      title: isHi ? "अदरक एवं लहसुन लेह्यम" : "Ginger & Garlic Lahyam",
      categoryBadge: isHi ? "सिनर्जिस्टिक अवलेह" : "Synergistic Polyherbal",
      category: "patent_or_proprietary" as FormulationCategory,
      statute: isHi ? "धारा 3(e) अप्रत्याशित प्रभाव" : "Section 3(e) Synergism Standard",
      description: isHi
        ? "अदरक, लहसुन और त्रिकटु का मिश्रण। केवल मात्र मिश्रण पर पेटेंट वर्जित है जब तक कि प्रायोगिक रूप से अप्रत्याशित सिनर्जिस्टिक प्रभाव सिद्ध न हो।"
        : "Classical ginger and garlic rasayana. To overcome the Section 3(e) mere admixture bar, quantitative synergistic bio-enhancement must be demonstrated.",
      query: isHi
        ? "क्या दो ज्ञात आयुर्वेदिक जड़ी-बूटियों के संयोजन पर धारा 3(e) के तहत पेटेंट मिल सकता है?"
        : "What experimental data is required to overcome the Section 3(e) mere admixture bar for a polyherbal formulation?",
    },
  ];

  /* Statutory Pillars */
  const pillars = [
    {
      id: "patents",
      title: isHi ? "भारतीय पेटेंट अधिनियम, 1970" : "The Patents Act, 1970",
      badge: isHi ? "पारंपरिक ज्ञान व सिनर्जी" : "TKDL & Synergism Bars",
      icon: "⚖️",
      description: isHi
        ? "धारा 3(p) पारंपरिक ज्ञान बार, धारा 3(d) प्रभावशीलता परीक्षण, और धारा 3(e) सिनर्जिस्टिक फॉर्मूलेशन सुरक्षा।"
        : "Section 3(p) Traditional Knowledge bar, Section 3(d) efficacy thresholds, and Section 3(e) synergistic combinations.",
      query: isHi
        ? "क्या चरक संहिता के शास्त्रीय नुस्खे पर धारा 3(p) के तहत भारत में पेटेंट मिल सकता है?"
        : "Can I obtain a product patent in India for an unmodified classical turmeric and neem wound formulation described in Charaka Samhita?",
      category: "classical_generic" as FormulationCategory,
      accentBorder: "border-[#7FB53D]/30",
    },
    {
      id: "bda",
      title: isHi ? "जैव विविधता अधिनियम, 2002" : "Biological Diversity Act, 2002",
      badge: isHi ? "राष्ट्रीय जैव विविधता प्राधिकरण" : "NBA Clearances & ABS",
      icon: "🌿",
      description: isHi
        ? "धारा 3 विदेशी संस्थाओं हेतु अनुमति, और धारा 6 भारतीय जैविक संसाधनों पर आधारित पेटेंट पूर्व अनुमति।"
        : "Section 3 foreign entity access permits, and Section 6 mandatory National Biodiversity Authority (NBA) prior clearance for IP filings.",
      query: isHi
        ? "क्या किसी विदेशी कंपनी को भारतीय जैविक संसाधनों पर आधारित पेटेंट दाखिल करने से पहले NBA से अनुमति लेनी होगी?"
        : "Does a foreign company need prior approval from the National Biodiversity Authority before filing a patent based on Indian biological resources?",
      category: "patent_or_proprietary" as FormulationCategory,
      accentBorder: "border-[#7FB53D]/30",
    },
    {
      id: "dca",
      title: isHi ? "औषधि एवं प्रसाधन सामग्री अधिनियम, 1940" : "Drugs & Cosmetics Act, 1940",
      badge: isHi ? "नियम 122E व शास्त्रीय मानक" : "Rule 122E & ASU Standards",
      icon: "🧪",
      description: isHi
        ? "धारा 3(a) प्रथम अनुसूची ग्रंथ, धारा 3(h) प्रोप्राइटरी औषधि, और नियम 122E न्यूनतम 4-मार्कर फाइटोफार्मास्युटिकल मानक।"
        : "Section 3(a) First Schedule classical drugs, Section 3(h) P&P medicines, and Rule 122E 4-bioactive marker phytopharmaceutical standards.",
      query: isHi
        ? "नियम 122E के तहत फाइटोफार्मास्युटिकल दवा के लिए न्यूनतम बायोएक्टिव मार्कर आवश्यकताएं क्या हैं?"
        : "What are the minimum bioactive marker requirements and regulatory standards for a phytopharmaceutical drug under Rule 122E?",
      category: "phytopharmaceutical" as FormulationCategory,
      accentBorder: "border-[#7FB53D]/30",
    },
    {
      id: "fssai",
      title: isHi ? "FSSAI (आयुर्वेद आहार) विनियम, 2022" : "FSSAI (Ayurveda Aahar) 2022",
      badge: isHi ? "खाद्य बनाम औषधीय सीमा" : "Food vs Drug Claims",
      icon: "🍵",
      description: isHi
        ? "विनियम 3 पोषण और आहार सिद्धांत, और विनियम 5 रोग निवारण/इलाज के दावों पर स्पष्ट वैधानिक प्रतिबंध।"
        : "Regulation 3 classical dietary preparations, and Regulation 5 strict prohibitions on advertising therapeutic disease cure claims.",
      query: isHi
        ? "क्या आयुर्वेद आहार उत्पाद मधुमेह को ठीक करने का दावा कर सकते हैं?"
        : "Can an Ayurveda Aahar herbal tea or nutritional supplement advertise claims to treat or cure diabetes under FSSAI regulations?",
      category: "ayurveda_aahar_nutraceutical" as FormulationCategory,
      accentBorder: "border-[#7FB53D]/30",
    },
  ];

  /* Interactive Tools */
  const tools = [
    {
      id: "chat",
      tab: "chat" as const,
      icon: MessageSquare,
      title: isHi ? "सांविधिक नियामक सहायक" : "Regulatory Intelligence Chat",
      tag: isHi ? "हाइब्रिड आरएजी व सटीक संदर्भ" : "Citation-Grounded RAG",
      desc: isHi
        ? "भारतीय पेटेंट, जैव विविधता एवं औषधि नियमों पर आधारित वास्तविक राजपत्र संदर्भों सहित त्वरित सांविधिक उत्तर।"
        : "Ask any legal question to receive citation-grounded answers strictly verified against official Indian Acts and Gazette notifications.",
      cta: isHi ? "सहायक शुरू करें" : "Start Regulatory Chat",
    },
    {
      id: "classifier",
      tab: "classifier" as const,
      icon: Sparkles,
      title: isHi ? "फॉर्मूलेशन क्लासिफायर विजार्ड" : "Formulation Classifier Wizard",
      tag: isHi ? "4-चरणीय निर्णय वृक्ष" : "4-Step Decision Tree",
      desc: isHi
        ? "अपने उत्पाद के घटकों और दावों के आधार पर शास्त्रीय, फाइटोफार्मास्युटिकल या आयुर्वेद आहार श्रेणी का निर्धारण करें।"
        : "Answer simple multi-choice questions to determine your product's regulatory posture, licensing requirements, and IP eligibility.",
      cta: isHi ? "विजार्ड शुरू करें" : "Launch Classifier",
    },
    {
      id: "comparator",
      tab: "comparator" as const,
      icon: Scale,
      title: isHi ? "द्विपक्षीय कानूनी तुलना" : "Side-by-Side Regime Comparator",
      tag: isHi ? "भारतीय कानून बनाम अंतरराष्ट्रीय संधियां" : "National vs International",
      desc: isHi
        ? "भारतीय पेटेंट और जैव विविधता कानूनों की TRIPS, नागोया प्रोटोकॉल और WIPO संधियों से सीधी तुलना।"
        : "Compare Indian statutory provisions with TRIPS, Nagoya Protocol, and global standards to plan international IP filings safely.",
      cta: isHi ? "तुलना देखें" : "Compare Regimes",
    },
    {
      id: "investigate",
      tab: "investigate" as const,
      icon: ShieldCheck,
      title: isHi ? "बौद्धिक संपदा जांच इंजन" : "IP Investigation Engine",
      tag: isHi ? "पेटेंट, शोध व TKDL तुलना" : "Prior Art & Risk Dossier",
      desc: isHi
        ? "अपने नुस्खे का विवरण दें और पेटेंट, शोध पत्रों, TKDL व नियमों के विरुद्ध स्वतः जोखिम व तुलनात्मक रिपोर्ट पाएं।"
        : "Extract structured formulation elements, cross-search global patents, research, and traditional knowledge, and generate an evidence-backed dossier.",
      cta: isHi ? "जांच शुरू करें" : "Launch Investigation",
    },
  ];

  return (
    <div className="relative space-y-20 sm:space-y-28 pb-16">
      {/* FLOATING BOTANICAL LEAF ACCENTS */}
      <div className="absolute top-6 right-8 pointer-events-none animate-float hidden lg:block z-0">
        <BotanicalLeaf size={46} rotation={-25} />
      </div>
      <div className="absolute top-48 left-2 pointer-events-none animate-float-reverse hidden lg:block z-0">
        <BotanicalLeaf size={38} rotation={45} flip />
      </div>
      <div className="absolute top-[850px] right-4 pointer-events-none animate-leaf-drift hidden lg:block z-0">
        <BotanicalLeaf size={42} rotation={15} />
      </div>
      <div className="absolute top-[1650px] left-6 pointer-events-none animate-float hidden lg:block z-0">
        <BotanicalLeaf size={36} rotation={-40} />
      </div>

      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden pt-4 sm:pt-10 pb-8">
        {/* Soft Ambient Glows */}
        <div className="absolute top-0 right-1/4 w-80 h-80 bg-[#7FB53D]/12 rounded-full blur-3xl pointer-events-none animate-float" />
        <div className="absolute bottom-0 left-10 w-96 h-96 bg-[#DEEED9]/70 rounded-full blur-3xl pointer-events-none animate-float-reverse" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center relative z-10">
          {/* Hero Left: Luxury Editorial Headline & Action CTAs */}
          <div className="lg:col-span-7 space-y-7">
            {/* Pill Tag */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#DEEED9]/90 border border-[#7FB53D]/40 text-xs font-bold text-[#2D5A27] shadow-xs backdrop-blur-xs">
              <Leaf className="w-4 h-4 text-[#7FB53D]" />
              <span className="tracking-wide uppercase text-[11px]">
                {isHi
                  ? "आयुर्वेद बौद्धिक संपदा एवं नियामक एआई इंटेलिजेंस"
                  : "Ayurveda IP & Regulatory Intelligence Platform"}
              </span>
            </div>

            {/* Headline with Luxury Editorial Typography */}
            <h1 className="text-4xl sm:text-6xl lg:text-[62px] font-serif-luxury font-bold text-[#1E2D24] tracking-tight leading-[1.08]">
              {isHi ? (
                <>
                  शास्त्रीय आयुर्वेद का गौरव,{" "}
                  <span className="text-[#7FB53D] italic">वैधानिक सुरक्षा</span>{" "}
                  के साथ
                </>
              ) : (
                <>
                  Overall wellness through{" "}
                  <span className="text-[#7FB53D] italic font-semibold">
                    Ayurveda
                  </span>
                  , Grounded in Law
                </>
              )}
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-[#4B6354] leading-relaxed max-w-2xl font-normal font-sans">
              {isHi
                ? "भारतीय पेटेंट अधिनियम 1970, जैव विविधता अधिनियम (NBA), ड्रग्स एंड कॉस्मेटिक्स एक्ट एवं FSSAI आयुर्वेद आहार के लिए 100% सांविधिक संदर्भों से प्रमाणित एआई मार्गदर्शन।"
                : "Authoritative, citation-grounded statutory intelligence for Ayurvedic formulations, phytopharmaceuticals, botanical patent filings, and FSSAI compliance."}
            </p>

            {/* Main Action Buttons */}
            <div className="flex flex-wrap items-center gap-3.5 pt-2">
              <button
                onClick={() => onNavigateToTab("chat")}
                className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-[#7FB53D] hover:bg-[#6EA033] text-white font-extrabold text-sm sm:text-base shadow-lg shadow-[#7FB53D]/30 transition-all hover:scale-[1.03] active:scale-[0.98] cursor-pointer"
              >
                <MessageSquare className="w-5 h-5" />
                <span>
                  {isHi ? "नियामक सहायक से पूछें" : "Ask Regulatory Assistant"}
                </span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              <button
                onClick={() => onNavigateToTab("classifier")}
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full bg-[#DEEED9] hover:bg-[#cde4c7] text-[#2D5A27] font-extrabold text-sm sm:text-base border border-[#7FB53D]/40 transition-all hover:scale-[1.03] active:scale-[0.98] cursor-pointer shadow-xs"
              >
                <Sparkles className="w-5 h-5 text-[#7FB53D]" />
                <span>
                  {isHi ? "फॉर्मूलेशन क्लासिफाई करें" : "Classify Formulation"}
                </span>
              </button>

              <button
                onClick={() => onNavigateToTab("comparator")}
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-full bg-white hover:bg-slate-50 text-[#1E2D24] font-bold text-sm border border-[#D8EADB] transition-colors shadow-xs cursor-pointer"
              >
                <Scale className="w-4 h-4 text-[#7FB53D]" />
                <span>{isHi ? "कानूनी तुलना" : "Compare Regimes"}</span>
              </button>

              <button
                onClick={() => onNavigateToTab("investigate")}
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-full bg-[#1E2D24] hover:bg-[#2D5A27] text-white font-bold text-sm shadow-md transition-all hover:scale-[1.03] active:scale-[0.98] cursor-pointer"
              >
                <ShieldCheck className="w-4 h-4 text-[#7FB53D]" />
                <span>{isHi ? "IP जांच इंजन" : "IP Investigation"}</span>
              </button>
            </div>

            {/* Trust Badges */}
            <div className="pt-2 flex flex-wrap items-center gap-5 text-xs sm:text-sm font-semibold text-[#4B6354]">
              <span className="inline-flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#7FB53D]" />
                {isHi
                  ? "शून्य भ्रम (Zero Hallucination)"
                  : "Zero-Hallucination Firewall"}
              </span>
              <span className="inline-flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#7FB53D]" />
                {isHi ? "100% राजपत्र प्रमाणित" : "100% Gazette Grounded"}
              </span>
              <span className="inline-flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#7FB53D]" />
                {isHi ? "द्विभाषी (हिंदी + EN)" : "Bilingual (EN + हिंदी)"}
              </span>
            </div>
          </div>

          {/* Hero Right: Arched Botanical Picture Frame */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="relative w-full max-w-md sm:max-w-lg">
              {/* Arched Outer Vessel */}
              <div className="ayur-treatment-arch bg-gradient-to-b from-[#DEEED9] to-white p-3 sm:p-4 border border-[#7FB53D]/35 shadow-2xl relative overflow-hidden">
                {/* Embedded Botanical Artwork */}
                <div className="relative w-full h-80 sm:h-96 rounded-t-[105px] rounded-b-2xl overflow-hidden shadow-inner">
                  <Image
                    src="/images/ayurveda_hero.jpg"
                    alt="Ayurvedic Botanical Remedies"
                    fill
                    priority
                    className="object-cover object-center transform hover:scale-105 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#1E2D24]/85 via-transparent to-transparent" />

                  {/* Overlaid Title */}
                  <div className="absolute bottom-4 left-4 right-4 text-white">
                    <span className="text-[10px] uppercase tracking-widest font-extrabold text-[#7FB53D] bg-white/95 px-2.5 py-0.5 rounded-full inline-block mb-1 shadow-xs">
                      {isHi ? "सांविधिक सुरक्षा" : "Statutory Assurance"}
                    </span>
                    <h4 className="text-base sm:text-lg font-serif-luxury font-bold text-white drop-shadow-sm">
                      {isHi
                        ? "प्रामाणिक आयुर्वेदिक ज्ञान का संरक्षण"
                        : "Heritage Preserved, Innovation Protected"}
                    </h4>
                  </div>
                </div>

                {/* Floating Micro-Pill Indicators */}
                <div className="mt-3.5 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-xl bg-white border border-[#DEEED9] shadow-xs">
                    <p className="font-extrabold text-[#7FB53D] text-sm">
                      Sec 3(p)
                    </p>
                    <p className="text-[10px] text-slate-500 font-medium truncate">
                      TK Bar
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-white border border-[#DEEED9] shadow-xs">
                    <p className="font-extrabold text-[#2D5A27] text-sm">
                      NBA Sec 6
                    </p>
                    <p className="text-[10px] text-slate-500 font-medium truncate">
                      ABS Approval
                    </p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-white border border-[#DEEED9] shadow-xs">
                    <p className="font-extrabold text-amber-600 text-sm">
                      Rule 122E
                    </p>
                    <p className="text-[10px] text-slate-500 font-medium truncate">
                      4 Markers
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. OUR AYURVEDIC FORMULATION & STATUTORY MODULES (Matching Reference Style) */}
      <section className="space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-2.5">
          <span className="text-xs font-bold uppercase tracking-widest text-[#7FB53D]">
            {isHi ? "शास्त्रीय एवं आधुनिक औषधियां" : "Botanical Intelligence"}
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight">
            {isHi ? "हमारे हर्बल एवं वैधानिक प्रारूप" : "Our Herbal Formulations & Guidance"}
          </h2>
          <p className="text-xs sm:text-sm text-[#4B6354] font-sans">
            {isHi
              ? "पारंपरिक ग्रंथों से लेकर फाइटोफार्मास्युटिकल मानकों तक, प्रत्येक श्रेणी के लिए वैधानिक स्पष्टता।"
              : "Explore statutory clearances, TKDL protections, and clinical standards across classical and proprietary formulations."}
          </p>
        </div>

        {/* 4 Arched Herbal Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-7">
          {treatments.map((item) => (
            <div
              key={item.id}
              className="ayur-card ayur-arch-lg p-4 sm:p-5 flex flex-col justify-between hover:shadow-2xl transition-all duration-300 group hover:-translate-y-2 border-[#D8EADB] bg-white relative overflow-hidden"
            >
              <div className="space-y-4">
                {/* Arched Image Header with Green Arch Frame */}
                <div className="ayur-treatment-arch bg-gradient-to-b from-[#7FB53D] to-[#5B8C2A] p-2 relative overflow-hidden shadow-inner">
                  <div className="relative w-full h-44 rounded-t-[100px] rounded-b-xl overflow-hidden bg-white">
                    <Image
                      src={item.image}
                      alt={item.title}
                      fill
                      className="object-cover object-center group-hover:scale-108 transition-transform duration-500"
                    />
                    <div className="absolute bottom-2 inset-x-2 flex justify-center">
                      <span className="text-[10px] font-extrabold px-3 py-0.5 rounded-full bg-white/95 text-[#2D5A27] shadow-md border border-[#DEEED9] backdrop-blur-xs whitespace-nowrap">
                        {item.categoryBadge}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="space-y-1.5 text-center px-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#7FB53D] block">
                    {item.statute}
                  </span>
                  <h3 className="text-lg sm:text-xl font-serif-luxury font-bold text-[#1E2D24] group-hover:text-[#7FB53D] transition-colors leading-tight">
                    {item.title}
                  </h3>
                  <p className="text-xs text-[#4B6354] leading-relaxed line-clamp-3 pt-1 font-sans">
                    {item.description}
                  </p>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 mt-3 border-t border-[#DEEED9]">
                <button
                  onClick={() =>
                    onNavigateToTab("chat", item.query, item.category)
                  }
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-full bg-[#F3FFFB] group-hover:bg-[#7FB53D] text-[#2D5A27] group-hover:text-white font-bold text-xs border border-[#DEEED9] group-hover:border-[#7FB53D] transition-all cursor-pointer shadow-xs"
                >
                  <span>{isHi ? "वैधानिक संदर्भ देखें" : "Explore Guidance"}</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. THE 3 CORE INTERACTIVE CAPABILITIES (Feature Suite) */}
      <section className="space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-2.5">
          <span className="text-xs font-bold uppercase tracking-widest text-[#7FB53D]">
            {isHi ? "तीन मुख्य उपकरण" : "Interactive Capabilities"}
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight">
            {isHi ? "उपयोग शुरू करने के लिए चुनें" : "Select a Specialized Tool"}
          </h2>
          <p className="text-xs sm:text-sm text-[#4B6354] font-sans">
            {isHi
              ? "प्रत्येक उपकरण वास्तविक सांविधिक कानूनों और कड़े सत्यापन तंत्र से संचालित होता है।"
              : "Launch any of our three dedicated intelligence tools designed for researchers, patent agents, and manufacturers."}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-7">
          {tools.map((tool) => {
            const Icon = tool.icon;
            return (
              <div
                key={tool.id}
                className="ayur-card ayur-arch-lg p-6 sm:p-8 flex flex-col justify-between hover:shadow-2xl transition-all duration-300 group hover:-translate-y-2 border-[#D8EADB] bg-white relative overflow-hidden"
              >
                <div className="space-y-4">
                  {/* Top Badge & Icon */}
                  <div className="flex items-center justify-between">
                    <div className="w-13 h-13 rounded-2xl bg-[#DEEED9] flex items-center justify-center text-[#7FB53D] group-hover:bg-[#7FB53D] group-hover:text-white transition-colors shadow-xs">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-[#F3FFFB] text-[#2D5A27] border border-[#DEEED9]">
                      {tool.tag}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-xl sm:text-2xl font-serif-luxury font-bold text-[#1E2D24] group-hover:text-[#7FB53D] transition-colors">
                    {tool.title}
                  </h3>

                  {/* Description */}
                  <p className="text-xs sm:text-sm text-[#4B6354] leading-relaxed font-sans font-normal">
                    {tool.desc}
                  </p>
                </div>

                {/* Launch Button */}
                <div className="pt-6 mt-4 border-t border-[#DEEED9]">
                  <button
                    onClick={() => onNavigateToTab(tool.tab)}
                    className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-[#F3FFFB] group-hover:bg-[#7FB53D] text-[#2D5A27] group-hover:text-white font-bold text-xs sm:text-sm border border-[#DEEED9] group-hover:border-[#7FB53D] transition-all shadow-xs cursor-pointer"
                  >
                    <span>{tool.cta}</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. FOUR STATUTORY PILLARS WITH 1-CLICK QUERIES */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2.5">
          <span className="text-xs font-bold uppercase tracking-widest text-[#7FB53D]">
            {isHi ? "वैधानिक आधारस्तंभ" : "Four Statutory Pillars"}
          </span>
          <h2 className="text-3xl sm:text-4xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight">
            {isHi ? "भारतीय कानून एवं नियामक व्यवस्था" : "Grounded Across 4 Key Statutes"}
          </h2>
          <p className="text-xs sm:text-sm text-[#4B6354] font-sans">
            {isHi
              ? "प्रत्येक वैधानिक क्षेत्र के प्रमुख प्रावधानों पर एक-क्लिक से वास्तविक विश्लेषण देखें।"
              : "Click any statutory pillar below to inspect its boundaries and launch a pre-grounded live query."}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {pillars.map((pillar) => (
            <div
              key={pillar.id}
              className={`ayur-arch bg-white border ${pillar.accentBorder} p-6 shadow-xs hover:shadow-xl transition-all duration-300 flex flex-col justify-between group hover:-translate-y-1`}
            >
              <div className="space-y-3.5">
                {/* Top Pill & Icon */}
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{pillar.icon}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#DEEED9] text-[#2D5A27] border border-[#7FB53D]/20">
                    {pillar.badge}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-base font-serif-luxury font-bold text-[#1E2D24] group-hover:text-[#7FB53D] transition-colors leading-snug">
                  {pillar.title}
                </h3>

                {/* Description */}
                <p className="text-xs text-[#4B6354] leading-relaxed font-sans">
                  {pillar.description}
                </p>
              </div>

              {/* Action Chip / 1-Click Launch */}
              <div className="pt-5 mt-4 border-t border-[#D8EADB]">
                <button
                  onClick={() =>
                    onNavigateToTab("chat", pillar.query, pillar.category)
                  }
                  className="w-full text-left p-3 rounded-2xl bg-[#F3FFFB] hover:bg-[#DEEED9] border border-[#DEEED9] hover:border-[#7FB53D]/50 transition-all group/btn cursor-pointer shadow-2xs"
                >
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#7FB53D] block mb-1">
                    {isHi ? "उदाहरण प्रश्न चलाएं" : "Run Live Query"}
                  </span>
                  <p className="text-xs font-medium text-[#1E2D24] line-clamp-2 group-hover/btn:text-[#2D5A27]">
                    &ldquo;{pillar.query}&rdquo;
                  </p>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. HERITAGE PROTECTION & SERENE BANNER */}
      <section className="relative overflow-hidden ayur-arch-lg shadow-2xl border border-[#7FB53D]/30">
        <div className="relative w-full min-h-[360px] sm:min-h-[400px]">
          <Image
            src="/images/ayurveda_heritage.jpg"
            alt="Traditional Ayurvedic Heritage"
            fill
            className="object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#1E2D24]/95 via-[#1E2D24]/85 to-[#1E2D24]/60" />

          {/* Banner Content */}
          <div className="relative z-10 p-6 sm:p-12 lg:p-16 max-w-3xl space-y-5 text-white flex flex-col justify-center h-full">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 text-emerald-200 border border-white/20 text-xs font-bold w-fit">
              <ShieldCheck className="w-4 h-4 text-[#7FB53D]" />
              <span>
                {isHi
                  ? "पारंपरिक ज्ञान डिजिटल लाइब्रेरी (TKDL) सुरक्षा"
                  : "TKDL Defended & ABS Compliant"}
              </span>
            </div>

            <h3 className="text-3xl sm:text-4xl lg:text-5xl font-serif-luxury font-bold tracking-tight leading-tight">
              {isHi
                ? "प्राचीन ज्ञान का संरक्षण, भविष्य के अनुपालन का निर्माण"
                : "Defending 5,000 Years of Heritage, Empowering Compliant Innovation"}
            </h3>

            <p className="text-xs sm:text-sm text-emerald-100/90 leading-relaxed font-sans font-normal">
              {isHi
                ? "सहयाक का शून्य-भ्रम इंजन सुनिश्चित करता है कि शास्त्रीय औषधियां पेटेंट दुरुपयोग से सुरक्षित रहें और आधुनिक फाइटोफार्मास्युटिकल नवाचारों को स्पष्ट कानूनी मार्ग मिले।"
                : "From classical Charaka Samhita recipes to standardized Rule 122E bioactive fractions, Sahayak provides transparent legal clarity without risking intellectual property exposure."}
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-4">
              <button
                onClick={() =>
                  onNavigateToTab(
                    "chat",
                    "Can I obtain a product patent in India for an unmodified classical turmeric and neem wound formulation described in Charaka Samhita?"
                  )
                }
                className="px-7 py-3.5 rounded-full bg-[#7FB53D] hover:bg-[#6EA033] text-white font-bold text-xs sm:text-sm shadow-lg shadow-black/25 transition-all hover:scale-105 cursor-pointer flex items-center gap-2"
              >
                <span>
                  {isHi ? "नीम व हल्दी पेटेंट केस देखें" : "Explore Classical TK Defense"}
                </span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 6. INSTANT CONSULTATION / QUERY LAUNCHPAD (Matching Appointment Form Style) */}
      <section className="ayur-arch-lg bg-white border border-[#D8EADB] p-8 sm:p-12 shadow-xl relative overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          <div className="lg:col-span-5 space-y-4">
            <span className="text-xs font-bold uppercase tracking-widest text-[#7FB53D]">
              {isHi ? "तुरंत वैधानिक परामर्श" : "Statutory Assessment"}
            </span>
            <h2 className="text-3xl sm:text-4xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight leading-tight">
              {isHi
                ? "अपने फॉर्मूलेशन का कानूनी विश्लेषण शुरू करें"
                : "Enter Your Formulation or IP Inquiry"}
            </h2>
            <p className="text-xs sm:text-sm text-[#4B6354] leading-relaxed font-sans">
              {isHi
                ? "किसी भी आयुर्वेदिक जड़ी-बूटी, पेटेंट धारा, या फाइटोफार्मास्युटिकल नियम पर सत्यापित राजपत्र संदर्भ प्राप्त करें।"
                : "Type your query below to launch an instant AI session grounded against verified statutory provisions and official gazette standards."}
            </p>
          </div>

          <div className="lg:col-span-7">
            <form
              onSubmit={handleQuickSubmit}
              className="bg-[#F6FAF4] p-5 sm:p-6 rounded-3xl border border-[#DEEED9] space-y-4 shadow-inner"
            >
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#2D5A27] flex items-center gap-1.5">
                  <Leaf className="w-3.5 h-3.5 text-[#7FB53D]" />
                  <span>{isHi ? "आपका प्रश्न या फॉर्मूलेशन विवरण" : "Your Legal Question or Formulation Details"}</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={quickQuery}
                    onChange={(e) => setQuickQuery(e.target.value)}
                    placeholder={
                      isHi
                        ? "उदा: क्या हल्दी और नीम के अर्क पर भारत में पेटेंट मिल सकता है?"
                        : "e.g. Can I patent a standardized turmeric extract under Rule 122E?"
                    }
                    className="w-full px-4 py-3.5 rounded-2xl bg-white border border-[#D8EADB] focus:border-[#7FB53D] focus:ring-2 focus:ring-[#7FB53D]/20 outline-none text-xs sm:text-sm text-[#1E2D24] transition-all pr-12 shadow-2xs"
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl bg-[#7FB53D] hover:bg-[#6EA033] text-white flex items-center justify-center transition-transform hover:scale-105 cursor-pointer shadow-xs"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Quick Presets */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-[11px] font-bold text-[#4B6354]">
                  {isHi ? "सुझाव:" : "Quick Ideas:"}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    onNavigateToTab(
                      "chat",
                      "Can I obtain a product patent in India for an unmodified classical turmeric and neem formulation?"
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-[#DEEED9] text-[#2D5A27] hover:border-[#7FB53D] transition-colors cursor-pointer"
                >
                  Section 3(p) TK Bar
                </button>
                <button
                  type="button"
                  onClick={() =>
                    onNavigateToTab(
                      "chat",
                      "What are the 4-marker requirements for a phytopharmaceutical under Rule 122E?"
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-[#DEEED9] text-[#2D5A27] hover:border-[#7FB53D] transition-colors cursor-pointer"
                >
                  Rule 122E Standard
                </button>
                <button
                  type="button"
                  onClick={() =>
                    onNavigateToTab(
                      "chat",
                      "Do foreign entities need NBA Form III approval before filing Indian patents?"
                    )
                  }
                  className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-[#DEEED9] text-[#2D5A27] hover:border-[#7FB53D] transition-colors cursor-pointer"
                >
                  NBA Sec 6 ABS
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
};
