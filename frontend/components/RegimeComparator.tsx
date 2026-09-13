"use client";

import React, { useState } from "react";
import { translations } from "@/lib/translations";
import { Scale, Globe, CheckCircle, Leaf } from "lucide-react";

interface RegimeComparatorProps {
  language?: "en" | "hi";
}

interface RegimeRow {
  topic: string;
  topicHi: string;
  indiaStatute: string;
  indiaRule: string;
  indiaRuleHi: string;
  intlStatute: string;
  intlRule: string;
  intlRuleHi: string;
  keyTakeaway: string;
  keyTakeawayHi: string;
}

const REGIME_DATA: RegimeRow[] = [
  {
    topic: "Traditional Knowledge & Patentability",
    topicHi: "पारंपरिक ज्ञान एवं पेटेंट पात्रता",
    indiaStatute: "The Patents Act, 1970 — Section 3(p)",
    indiaRule: "Strict Statutory Bar: Inventions that are traditional knowledge or aggregations/duplications of known properties of traditionally known components are non-patentable. Defended globally via TKDL prior art.",
    indiaRuleHi: "सख्त वैधानिक रोक: कोई भी आविष्कार जो पारंपरिक ज्ञान या पारंपरिक अवयवों का मात्र संकलन है, पेटेंट योग्य नहीं है। TKDL के माध्यम से वैश्विक रक्षा।",
    intlStatute: "TRIPS Art. 27.3(b) & WIPO GRATK Treaty (2024)",
    intlRule: "Allows sui generis TK regimes at national discretion. The new 2024 WIPO GRATK Treaty mandates patent applicants to disclose the country of origin/indigenous source of genetic resources and associated traditional knowledge.",
    intlRuleHi: "राष्ट्रीय स्तर पर विशेष अधिकार की अनुमति। 2024 की WIPO GRATK संधि के तहत पेटेंट आवेदनों में आनुवंशिक संसाधनों और पारंपरिक ज्ञान के मूल देश का खुलासा करना अनिवार्य है।",
    keyTakeaway: "India explicitly excludes unmodified TK by statutory bar; international frameworks rely on mandatory origin disclosure and prior art challenges.",
    keyTakeawayHi: "भारत स्पष्ट रूप से कानूनन पेटेंट रोकता है; अंतरराष्ट्रीय व्यवस्था मूल देश के खुलासे पर निर्भर करती है।",
  },
  {
    topic: "Access and Benefit Sharing (ABS) for Biological Resources",
    topicHi: "जैव विविधता एवं लाभ साझाकरण (ABS)",
    indiaStatute: "Biological Diversity Act, 2002 — Sections 3 & 6",
    indiaRule: "Non-Indian entities/foreign participations MUST obtain prior approval from the National Biodiversity Authority (NBA) before accessing biological resources or applying for patents inside or outside India.",
    indiaRuleHi: "विदेशी कंपनियों या अनिवासी भारतीयों को भारतीय जैविक संसाधनों तक पहुँचने या पेटेंट दाखिल करने से पहले राष्ट्रीय जैव विविधता प्राधिकरण (NBA) से पूर्व अनुमति लेना अनिवार्य है।",
    intlStatute: "Nagoya Protocol on ABS & Convention on Biological Diversity (CBD)",
    intlRule: "Requires Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) for utilizing genetic resources and associated traditional knowledge with fair and equitable benefit sharing.",
    intlRuleHi: "पारस्परिक सहमति की शर्तों (MAT) और पूर्व सूचित सहमति (PIC) के तहत आनुवंशिक संसाधनों के उपयोग पर उचित लाभ साझा करना आवश्यक है।",
    keyTakeaway: "Filing an Indian bio-resource patent abroad without NBA approval violates criminal and civil provisions under Indian law.",
    keyTakeawayHi: "NBA की मंजूरी के बिना विदेश में भारतीय जैविक संसाधन पर पेटेंट दाखिल करना भारतीय कानून का उल्लंघन है।",
  },
  {
    topic: "Phytopharmaceutical Drug Standardization",
    topicHi: "फाइटोफार्मास्युटिकल दवा मानकीकरण",
    indiaStatute: "Drugs and Cosmetics Act, 1940 — Rule 122E",
    indiaRule: "Mandates minimum 4 defined bioactive/phytochemical markers in standardized extract of medicinal plants. Requires preclinical safety, toxicity, and Schedule Y clinical trials.",
    indiaRuleHi: "औषधीय पौधों के अर्क में न्यूनतम 4 बायोएक्टिव मार्कर अनिवार्य हैं। शेड्यूल Y के तहत प्री-क्लिनिकल सुरक्षा और क्लिनिकल परीक्षण अनिवार्य।",
    intlStatute: "EMA Herbal Medicinal Products Directive (2004/24/EC) & US FDA Botanical Guidance",
    intlRule: "EU requires 30-year traditional use evidence (15 years within EU) for simplified registration. US FDA Botanical Drug guidance evaluates whole complex mixtures without requiring 4 single markers.",
    intlRuleHi: "यूरोपीय संघ में 30 वर्षों के पारंपरिक उपयोग का प्रमाण आवश्यक है। अमेरिकी FDA पूरे बॉटनिकल अर्क की समग्र प्रभावशीलता का मूल्यांकन करता है।",
    keyTakeaway: "India has a distinct statutory fast-track class (Rule 122E) specifically for standardized multi-marker herbal extracts.",
    keyTakeawayHi: "भारत में 4-मार्कर वाले मानकीकृत अर्क के लिए नियम 122E का विशिष्ट कानूनी प्रावधान है।",
  },
  {
    topic: "Ayurvedic Food & Dietary Disease Claims",
    topicHi: "आयुर्वेद आहार एवं रोग निवारण के दावे",
    indiaStatute: "FSSAI (Ayurveda Aahar) Regulations, 2022 — Section 5",
    indiaRule: "Prohibits any Ayurveda Aahar product from claiming to cure, treat, or mitigate any disease in humans. Package must prominently display the official Ayurveda Aahar logo.",
    indiaRuleHi: "किसी भी आयुर्वेद आहार उत्पाद पर मानव रोगों के इलाज या रोकथाम का दावा करने पर पूर्ण प्रतिबंध है। आधिकारिक लोगो लगाना अनिवार्य है।",
    intlStatute: "US DSHEA (1994) & Codex Alimentarius Guidelines",
    intlRule: "Permits structure/function claims (e.g. 'supports immune health') with mandatory disclaimer ('This statement has not been evaluated by the FDA'). Strict prohibition on disease treatment claims without NDA.",
    intlRuleHi: "संरचना/कार्य संबंधी दावों ('इम्युनिटी बढ़ाता है') की अनुमति है लेकिन अनिवार्य अस्वीकरण के साथ। रोग इलाज के दावों पर रोक।",
    keyTakeaway: "Ayurveda Aahar cannot market therapeutic disease cures under food license; therapeutic claims require a D&C drug license.",
    keyTakeawayHi: "आयुर्वेद आहार खाद्य लाइसेंस के तहत रोग इलाज का दावा नहीं कर सकता; इसके लिए औषधि लाइसेंस आवश्यक है।",
  },
];

export const RegimeComparator: React.FC<RegimeComparatorProps> = ({ language = "en" }) => {
  const [selectedTopic, setSelectedTopic] = useState<number>(0);
  const t = translations[language].comparator;

  return (
    <div className="w-full max-w-6xl mx-auto py-4 sm:py-8 px-2 sm:px-6 min-w-0">
      {/* Header */}
      <div className="text-center space-y-2 mb-6 sm:mb-8">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#DEEED9] text-[#2D5A27] text-xs font-bold border border-[#7FB53D]/30 shadow-xs">
          <Scale className="w-3.5 h-3.5 text-[#7FB53D] shrink-0" />
          <span>{language === "hi" ? "द्विपक्षीय नियामक तुलना" : "Side-by-Side Regulatory Matrix"}</span>
        </div>
        <h2 className="text-xl sm:text-3xl lg:text-4xl font-serif-luxury font-bold text-[#1E2D24] tracking-tight leading-tight px-2">
          {t.title}
        </h2>
        <p className="text-xs sm:text-sm text-[#4B6354] max-w-2xl mx-auto font-normal leading-relaxed px-2">
          {t.subtitle}
        </p>
      </div>

      {/* Topic Tabs */}
      <div className="w-full max-w-full overflow-hidden mb-6 sm:mb-8">
        <div className="flex overflow-x-auto gap-2 sm:gap-2.5 pb-2 justify-start sm:justify-center no-scrollbar w-full px-1">
          {REGIME_DATA.map((row, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedTopic(idx)}
              className={`px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-2xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap shrink-0 ${
                selectedTopic === idx
                  ? "bg-[#7FB53D] text-white shadow-md shadow-[#7FB53D]/25 scale-[1.02]"
                  : "bg-white text-[#1E2D24] border border-[#D8EADB] hover:bg-[#DEEED9]/40"
              }`}
            >
              {language === "hi" ? row.topicHi : row.topic}
            </button>
          ))}
        </div>
      </div>

      {/* Active Comparison Card */}
      {(() => {
        const item = REGIME_DATA[selectedTopic];
        return (
          <div className="ayur-card rounded-2xl sm:ayur-arch-lg shadow-xl overflow-hidden animate-in fade-in duration-150 w-full min-w-0">
            {/* Title Bar */}
            <div className="p-4 sm:p-6 bg-gradient-to-r from-[#2D5A27] to-[#1E431A] text-white flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-4">
              <div className="flex items-center gap-2.5 min-w-0">
                <Leaf className="w-5 h-5 text-[#7FB53D] shrink-0" />
                <h3 className="text-sm sm:text-lg font-extrabold break-words">
                  {language === "hi" ? item.topicHi : item.topic}
                </h3>
              </div>
              <span className="text-[10px] sm:text-[11px] font-bold uppercase px-2.5 sm:px-3 py-1 rounded-full bg-white/15 text-emerald-200 border border-white/20 shrink-0 self-start sm:self-auto">
                Regime Comparison
              </span>
            </div>

            {/* Side-by-side Matrix */}
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#D8EADB]">
              {/* India Column */}
              <div className="p-4 sm:p-8 space-y-4 bg-[#DEEED9]/20 min-w-0">
                <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-[#2D5A27]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#7FB53D] shrink-0" />
                  <span>{t.indiaHeader}</span>
                </div>

                <div className="p-3.5 sm:p-4 rounded-2xl bg-white border border-[#D8EADB] shadow-xs">
                  <span className="text-[11px] font-bold text-[#4B6354] uppercase tracking-wide block">
                    Statutory Instrument
                  </span>
                  <p className="text-xs sm:text-sm font-bold text-[#2D5A27] mt-1 break-words">
                    {item.indiaStatute}
                  </p>
                </div>

                <div className="text-xs sm:text-sm text-[#1E2D24] leading-relaxed space-y-2">
                  <span className="text-[11px] sm:text-xs font-bold text-[#4B6354] uppercase tracking-wide block">
                    Regulatory Provision & Rule
                  </span>
                  <p className="break-words">{language === "hi" ? item.indiaRuleHi : item.indiaRule}</p>
                </div>
              </div>

              {/* International Column */}
              <div className="p-4 sm:p-8 space-y-4 bg-[#F3FFFB] min-w-0">
                <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-[#2D5A27]">
                  <Globe className="w-3.5 h-3.5 text-[#7FB53D] shrink-0" />
                  <span>{t.intlHeader}</span>
                </div>

                <div className="p-3.5 sm:p-4 rounded-2xl bg-white border border-[#D8EADB] shadow-xs">
                  <span className="text-[11px] font-bold text-[#4B6354] uppercase tracking-wide block">
                    International Treaty / Regulation
                  </span>
                  <p className="text-xs sm:text-sm font-bold text-[#2D5A27] mt-1 break-words">
                    {item.intlStatute}
                  </p>
                </div>

                <div className="text-xs sm:text-sm text-[#1E2D24] leading-relaxed space-y-2">
                  <span className="text-[11px] sm:text-xs font-bold text-[#4B6354] uppercase tracking-wide block">
                    Global Rule & Standards
                  </span>
                  <p className="break-words">{language === "hi" ? item.intlRuleHi : item.intlRule}</p>
                </div>
              </div>
            </div>

            {/* Key Takeaway Banner */}
            <div className="p-4 sm:p-6 bg-[#FAF8F2] border-t border-[#D8EADB] flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-[#7FB53D] shrink-0 mt-0.5" />
              <div className="text-xs sm:text-sm text-[#1E2D24] min-w-0">
                <span className="font-extrabold text-[#2D5A27] mr-2">
                  {language === "hi" ? "प्रमुख निष्कर्ष:" : "Core Regulatory Takeaway:"}
                </span>
                <span className="leading-relaxed font-normal break-words">{language === "hi" ? item.keyTakeawayHi : item.keyTakeaway}</span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
