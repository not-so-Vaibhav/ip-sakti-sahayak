"""Investigation Report (Dossier) Generator for IP-SAKTI Sahayak.

Renders a complete investigation case into a structured markdown dossier
covering all 13 sections: case details, classification, formulation extraction,
sources searched, patent/research/TK findings, comparison matrix, risk assessment,
reasoning, confidence, uncertainties, recommended actions, and citations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from backend.app.investigation.models import (
    ComparisonMatrix,
    EvidenceSource,
    EvidenceSourceType,
    InvestigationCase,
    RiskAssessment,
    RiskLevel,
    StructuredFormulation,
)

logger = logging.getLogger(__name__)

# Bilingual section titles
SECTION_TITLES = {
    "en": {
        "main_title": "IP Investigation Report — IP-SAKTI Sahayak",
        "case_details": "1. Case Details",
        "classification": "2. Formulation Classification",
        "formulation": "3. Structured Formulation",
        "sources_searched": "4. Sources Searched",
        "patent_findings": "5. Patent Findings",
        "research_findings": "6. Research Findings",
        "tk_findings": "7. Traditional Knowledge & Classical Formulation Findings",
        "comparison_matrix": "8. Element-Wise Comparison Matrix",
        "risk_assessment": "9. Risk Assessment",
        "reasoning": "10. Reasoning & Evidence Trail",
        "confidence": "11. Confidence & Uncertainty",
        "actions": "12. Recommended Next Actions",
        "citations": "13. Full Citation List",
        "disclaimer": "Disclaimer",
    },
    "hi": {
        "main_title": "बौद्धिक संपदा जांच रिपोर्ट — IP-SAKTI सहायक",
        "case_details": "1. केस विवरण",
        "classification": "2. नुस्खा वर्गीकरण",
        "formulation": "3. संरचित नुस्खा",
        "sources_searched": "4. खोजे गए स्रोत",
        "patent_findings": "5. पेटेंट निष्कर्ष",
        "research_findings": "6. शोध निष्कर्ष",
        "tk_findings": "7. पारंपरिक ज्ञान एवं शास्त्रीय नुस्खा निष्कर्ष",
        "comparison_matrix": "8. तत्व-वार तुलना मैट्रिक्स",
        "risk_assessment": "9. जोखिम आकलन",
        "reasoning": "10. तर्क एवं प्रमाण श्रृंखला",
        "confidence": "11. विश्वसनीयता एवं अनिश्चितता",
        "actions": "12. अनुशंसित अगले कदम",
        "citations": "13. संपूर्ण उद्धरण सूची",
        "disclaimer": "अस्वीकरण",
    },
}

RISK_EMOJI = {
    RiskLevel.LOW: "🟢",
    RiskLevel.MEDIUM: "🟡",
    RiskLevel.HIGH: "🟠",
    RiskLevel.CRITICAL: "🔴",
}

DIMENSION_NAMES = {
    "en": {
        "novelty_risk": "Novelty Risk",
        "tk_overlap": "TK Overlap",
        "regulatory_complexity": "Regulatory Complexity",
        "abs_compliance": "ABS Compliance",
        "prior_art_exposure": "Prior Art Exposure",
    },
    "hi": {
        "novelty_risk": "नवीनता जोखिम",
        "tk_overlap": "पारंपरिक ज्ञान ओवरलैप",
        "regulatory_complexity": "नियामक जटिलता",
        "abs_compliance": "ABS अनुपालन",
        "prior_art_exposure": "पूर्व कला जोखिम",
    },
}

SOURCE_TYPE_LABELS = {
    "en": {
        EvidenceSourceType.PATENT: "Patent",
        EvidenceSourceType.RESEARCH_PAPER: "Research Paper",
        EvidenceSourceType.TK_SOURCE: "Traditional Knowledge",
        EvidenceSourceType.FORMULATION: "Classical Formulation",
        EvidenceSourceType.REGULATION: "Regulation",
    },
    "hi": {
        EvidenceSourceType.PATENT: "पेटेंट",
        EvidenceSourceType.RESEARCH_PAPER: "शोध पत्र",
        EvidenceSourceType.TK_SOURCE: "पारंपरिक ज्ञान",
        EvidenceSourceType.FORMULATION: "शास्त्रीय नुस्खा",
        EvidenceSourceType.REGULATION: "विनियमन",
    },
}


class ReportGenerator:
    """Renders investigation cases as structured markdown dossiers."""

    def render(self, case: InvestigationCase) -> str:
        """Render complete investigation report as markdown."""
        lang = case.language if case.language in ("en", "hi") else "en"
        t = SECTION_TITLES[lang]
        sections = []

        # Title
        sections.append(f"# {t['main_title']}\n")

        # 1. Case Details
        sections.append(f"## {t['case_details']}\n")
        sections.append(f"| Field | Value |")
        sections.append(f"|---|---|")
        sections.append(f"| Case ID | `{case.case_id}` |")
        sections.append(f"| Created | {case.created_at} |")
        sections.append(f"| Jurisdiction | {case.jurisdiction.title()} |")
        sections.append(f"| Language | {case.language.upper()} |")
        sections.append(f"| Status | {case.status.value if hasattr(case.status, 'value') else case.status} |")
        sections.append("")

        # 2. Classification
        sections.append(f"## {t['classification']}\n")
        cat = case.classification_category or "Not classified"
        sections.append(f"**Category:** `{cat}`\n")

        # 3. Structured Formulation
        sections.append(f"## {t['formulation']}\n")
        if case.formulation:
            f = case.formulation
            sections.append(f"> **Raw Input:** {f.raw_input}\n")

            if f.ingredients:
                sections.append("**Ingredients:**")
                for ing in f.ingredients:
                    val_str = f" ({ing.value})" if ing.value else ""
                    sections.append(f"- 🌿 {ing.name}{val_str}")
                sections.append("")

            if f.ratios:
                sections.append("**Ratios:**")
                for r in f.ratios:
                    sections.append(f"- ⚖️ {r.name}: {r.value or 'unspecified'}")
                sections.append("")

            if f.processes:
                sections.append("**Processes:**")
                for p in f.processes:
                    sections.append(f"- ⚗️ {p.name}")
                sections.append("")

            if f.dosage_forms:
                sections.append("**Dosage Forms:**")
                for d in f.dosage_forms:
                    sections.append(f"- 💊 {d.name}")
                sections.append("")

            if f.intended_uses:
                sections.append("**Intended Uses:**")
                for u in f.intended_uses:
                    sections.append(f"- 🎯 {u.name}")
                sections.append("")
        else:
            sections.append("*No formulation data extracted.*\n")

        # 4. Sources Searched
        sections.append(f"## {t['sources_searched']}\n")
        type_labels = SOURCE_TYPE_LABELS[lang]
        type_counts: Dict[EvidenceSourceType, int] = {}
        for src in case.evidence_sources:
            type_counts[src.source_type] = type_counts.get(src.source_type, 0) + 1

        sections.append("| Source Type | Count |")
        sections.append("|---|---|")
        for st, label in type_labels.items():
            count = type_counts.get(st, 0)
            sections.append(f"| {label} | {count} |")
        sections.append(f"| **Total** | **{len(case.evidence_sources)}** |")
        sections.append("")

        # 5-7. Findings by type
        for source_type, section_key in [
            (EvidenceSourceType.PATENT, "patent_findings"),
            (EvidenceSourceType.RESEARCH_PAPER, "research_findings"),
            (None, "tk_findings"),  # TK + FORMULATION combined
        ]:
            sections.append(f"## {t[section_key]}\n")

            if source_type is None:
                filtered = [
                    s for s in case.evidence_sources
                    if s.source_type in (EvidenceSourceType.TK_SOURCE, EvidenceSourceType.FORMULATION)
                ]
            else:
                filtered = [s for s in case.evidence_sources if s.source_type == source_type]

            if not filtered:
                sections.append("*No results found.*\n")
                continue

            for i, src in enumerate(filtered[:5], 1):
                overlap = ""
                if case.comparison_matrix:
                    ov = case.comparison_matrix.overlap_scores.get(src.source_id, 0)
                    overlap = f" | Overlap: **{ov:.0%}**"
                sections.append(f"### {i}. {src.title}")
                sections.append(f"- **ID:** {src.identifier or 'N/A'}")
                if src.publication_date:
                    sections.append(f"- **Date:** {src.publication_date}")
                sections.append(f"- **Relevance:** {src.relevance_score:.0%}{overlap}")
                if src.url:
                    sections.append(f"- **Source:** [{src.url}]({src.url})")
                sections.append(f"- **Excerpt:** {src.relevant_text[:300]}...")
                sections.append("")

        # 8. Comparison Matrix
        sections.append(f"## {t['comparison_matrix']}\n")
        if case.comparison_matrix and case.comparison_matrix.comparisons:
            cm = case.comparison_matrix
            # Build header
            source_headers = []
            source_ids_ordered = []
            for src in cm.evidence_sources[:8]:  # Limit columns
                label = src.title[:25] + "..." if len(src.title) > 25 else src.title
                source_headers.append(label)
                source_ids_ordered.append(src.source_id)

            header = "| Element | Type | User | " + " | ".join(source_headers) + " |"
            separator = "|---|---|---|" + "|".join(["---"] * len(source_headers)) + "|"
            sections.append(header)
            sections.append(separator)

            for comp in cm.comparisons:
                user_mark = "✓"
                source_marks = []
                for sid in source_ids_ordered:
                    if comp.matches.get(sid, False):
                        source_marks.append("✓")
                    else:
                        source_marks.append("✕")
                row = f"| {comp.element_name} | {comp.element_type} | {user_mark} | " + " | ".join(source_marks) + " |"
                sections.append(row)

            # Overlap row
            overlap_row = "| **Overlap %** | | | "
            for sid in source_ids_ordered:
                ov = cm.overlap_scores.get(sid, 0)
                overlap_row += f"**{ov:.0%}** | "
            sections.append(overlap_row)
            sections.append("")
        else:
            sections.append("*No comparison data available.*\n")

        # 9. Risk Assessment
        sections.append(f"## {t['risk_assessment']}\n")
        if case.risk_assessment:
            ra = case.risk_assessment
            dim_names = DIMENSION_NAMES[lang]

            # Overall risk banner
            emoji = RISK_EMOJI.get(ra.overall_risk, "⚪")
            sections.append(f"### Overall Risk: {emoji} **{ra.overall_risk.value}** (Confidence: {ra.overall_confidence:.0%})\n")

            sections.append("| Dimension | Level | Score |")
            sections.append("|---|---|---|")
            for dim in ra.dimensions:
                d_emoji = RISK_EMOJI.get(dim.level, "⚪")
                d_name = dim_names.get(dim.dimension.value, dim.dimension.value)
                sections.append(f"| {d_name} | {d_emoji} {dim.level.value} | {dim.score:.0%} |")
            sections.append("")
        else:
            sections.append("*No risk assessment available.*\n")

        # 10. Reasoning
        sections.append(f"## {t['reasoning']}\n")
        if case.risk_assessment:
            dim_names = DIMENSION_NAMES[lang]
            for dim in case.risk_assessment.dimensions:
                d_name = dim_names.get(dim.dimension.value, dim.dimension.value)
                sections.append(f"### {d_name}")
                sections.append(f"{dim.reasoning}\n")
                if dim.supporting_evidence:
                    sections.append(f"*Supporting evidence: {len(dim.supporting_evidence)} source(s)*\n")

        # 11. Confidence & Uncertainty
        sections.append(f"## {t['confidence']}\n")
        if case.risk_assessment:
            sections.append(f"**Overall Confidence:** {case.risk_assessment.overall_confidence:.0%}\n")
            if case.risk_assessment.uncertainties:
                sections.append("**Uncertainties:**")
                for u in case.risk_assessment.uncertainties:
                    sections.append(f"- ⚠️ {u}")
                sections.append("")

        # 12. Recommended Actions
        sections.append(f"## {t['actions']}\n")
        if case.risk_assessment and case.risk_assessment.recommended_actions:
            for i, action in enumerate(case.risk_assessment.recommended_actions, 1):
                sections.append(f"{i}. {action}")
            sections.append("")

        # 13. Full Citation List
        sections.append(f"## {t['citations']}\n")
        for i, src in enumerate(case.evidence_sources, 1):
            type_label = type_labels.get(src.source_type, src.source_type.value)
            url_str = f" — [{src.url}]({src.url})" if src.url else ""
            sections.append(
                f"{i}. **[{type_label}]** {src.title}"
                f"{' — ' + src.identifier if src.identifier else ''}"
                f"{url_str}"
            )
        sections.append("")

        # Disclaimer
        sections.append(f"---\n## {t['disclaimer']}\n")
        if lang == "hi":
            sections.append(
                "यह रिपोर्ट स्वचालित विश्लेषण पर आधारित है और कानूनी सलाह नहीं है। "
                "औपचारिक IP राय के लिए पंजीकृत पेटेंट एजेंट से परामर्श लें।"
            )
        else:
            sections.append(
                "This report is generated by automated analysis and does not constitute legal advice. "
                "Consult a registered patent attorney or qualified AYUSH legal practitioner for formal IP opinions and filings."
            )

        report = "\n".join(sections)
        logger.info(f"Report generated: {len(report)} chars, {len(case.evidence_sources)} citations")
        return report


report_generator_service = ReportGenerator()
