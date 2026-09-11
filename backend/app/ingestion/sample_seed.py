"""Sample seed legal documents for testing and running the ingestion pipeline."""

from typing import List
from backend.app.ingestion.chunker import RawInstrumentDocument


SAMPLE_DOCUMENTS: List[RawInstrumentDocument] = [
    RawInstrumentDocument(
        instrument_name="The Patents Act, 1970",
        jurisdiction="india",
        regime_category="patent",
        authority_level="primary_law",
        source_url="https://ipindia.gov.in/acts-patents.htm",
        effective_date="1972-04-20",
        last_amended_date="2024-03-15",
        default_formulation_relevance=["classical_generic", "patent_or_proprietary", "new_non_classical_drug", "phytopharmaceutical"],
        language="en",
        raw_content="""
CHAPTER II — Inventions Not Patentable

Section 3(p) — Traditional Knowledge Bar
An invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is not an invention within the meaning of this Act.
[relevance: classical_generic, patent_or_proprietary]

Section 3(d) — Mere Discovery of Known Substance Bar
The mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance or the mere discovery of any new property or new use for a known substance or of the mere use of a known process, machine or apparatus unless such known process results in a new product or employs at least one new reactant is not patentable. For the purposes of this clause, salts, esters, ethers, polymorphs, metabolites, pure form, particle size, isomers, mixtures of isomers, complexes, combinations and other derivatives of known substance shall be considered to be the same substance, unless they differ significantly in properties with regard to efficacy.
[relevance: patent_or_proprietary, new_non_classical_drug, phytopharmaceutical]

Section 3(e) — Mere Admixture Bar
A substance obtained by a mere admixture resulting only in the aggregation of the properties of the components thereof or a process for producing such substance is not patentable. Synergistic interaction between herbal components must be demonstrated with empirical data to overcome this bar.
[relevance: classical_generic, patent_or_proprietary, new_non_classical_drug]
""",
    ),
    RawInstrumentDocument(
        instrument_name="The Biological Diversity Act, 2002",
        jurisdiction="india",
        regime_category="abs",
        authority_level="primary_law",
        source_url="http://nbaindia.org/act/",
        effective_date="2003-02-05",
        last_amended_date="2023-08-03",
        default_formulation_relevance=["classical_generic", "patent_or_proprietary", "new_non_classical_drug", "phytopharmaceutical", "ayurveda_aahar_nutraceutical", "cosmetic"],
        language="en",
        raw_content="""
CHAPTER II — Regulation of Access to Biological Diversity

Section 3 — Certain persons not to undertake Biodiversity related activities without approval of National Biodiversity Authority
(1) No person referred to in sub-section (2) shall, without previous approval of the National Biodiversity Authority, obtain any biological resource occurring in India or knowledge associated thereto for research or for commercial utilisation or for bio-survey and bio-utilisation.
(2) The persons who shall be required to take the approval of the National Biodiversity Authority under sub-section (1) are the following, namely:
(a) a person who is not a citizen of India;
(b) a citizen of India, who is a non-resident as defined in clause (30) of section 2 of the Income-tax Act, 1961;
(c) a body corporate, association or organisation—
(i) not incorporated or registered in India; or
(ii) incorporated or registered in India under any law for the time being in force which has any non-Indian participation in its share capital or management.
[relevance: classical_generic, patent_or_proprietary, new_non_classical_drug, phytopharmaceutical, ayurveda_aahar_nutraceutical, cosmetic]

Section 6 — Application for intellectual property rights not to be made without approval of National Biodiversity Authority
(1) No person shall apply for any intellectual property right, by whatever name called, in or outside India for any invention based on any research or information on a biological resource obtained from India without obtaining the previous approval of the National Biodiversity Authority before making such application:
Provided that if a person applies for a patent, permission of the National Biodiversity Authority may be obtained after the acceptance of the patent but before the sealing of the patent by the patent authority concerned.
(2) The National Biodiversity Authority may, while granting the approval under this section, impose benefit sharing fee or royalty or conditions on the commercial utilisation of the intellectual property right.
[relevance: classical_generic, patent_or_proprietary, new_non_classical_drug, phytopharmaceutical]
""",
    ),
    RawInstrumentDocument(
        instrument_name="The Drugs and Cosmetics Act, 1940 & Rules, 1945",
        jurisdiction="india",
        regime_category="drug_regulatory",
        authority_level="primary_law",
        source_url="https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/",
        effective_date="1940-04-10",
        last_amended_date="2022-10-01",
        default_formulation_relevance=["classical_generic", "patent_or_proprietary", "new_non_classical_drug", "phytopharmaceutical"],
        language="en",
        raw_content="""
CHAPTER IV-A — Provisions Relating to Ayurvedic, Siddha and Unani Drugs

Section 3(a) — Ayurvedic, Siddha or Unani Drug Definition
"Ayurvedic, Siddha or Unani drug" includes all medicines intended for internal or external use for or in the diagnosis, treatment, mitigation or prevention of disease or disorder in human beings or animals, and manufactured exclusively in accordance with the formulae described in the authoritative books of Ayurvedic, Siddha and Unani systems of medicine specified in the First Schedule.
[relevance: classical_generic]

Section 3(h) — Patent or Proprietary Medicine in relation to Ayurvedic Systems
"Patent or proprietary medicine" in relation to Ayurvedic, Siddha or Unani systems of medicine means a drug which is a remedy or prescription presented in any form prepared exclusively from Ayurvedic, Siddha or Unani formulations described in or based on the formulae described in the authoritative books of Ayurvedic, Siddha or Unani systems of medicine, but does not include a medicine which is administered by parenteral route and also a formulation which is in accordance with the authoritative books.
[relevance: patent_or_proprietary]

Rule 122E — Phytopharmaceutical Drugs
A phytopharmaceutical drug is defined as purified and standardized fraction with defined minimum four bioactive or phytochemical markers of an extract of a medicinal plant or its part, for internal or external use of human beings or animals for diagnosis, treatment, mitigation, or prevention of any disease or disorder. Requires systematic preclinical safety, toxicity, and clinical trials under Schedule Y.
[relevance: phytopharmaceutical]
""",
    ),
    RawInstrumentDocument(
        instrument_name="Food Safety and Standards (Ayurveda Aahar) Regulations, 2022",
        jurisdiction="india",
        regime_category="food_regulatory",
        authority_level="rule",
        source_url="https://www.fssai.gov.in/",
        effective_date="2022-05-09",
        last_amended_date="2022-05-09",
        default_formulation_relevance=["ayurveda_aahar_nutraceutical"],
        language="en",
        raw_content="""
CHAPTER I — General Provisions

Section 3 — Definition of Ayurveda Aahar
"Ayurveda Aahar" means food prepared in accordance with the recipes or books/texts specified in Schedule A of these regulations, including products prepared for nutritional health and well-being. It does not include Ayurvedic drugs or medicines, proprietary Ayurvedic drugs, or cosmetics.

Section 5 — Labeling and Disease Cure Claims Prohibition
No person shall manufacture, pack, sell, offer for sale, or distribute any Ayurveda Aahar product with claims to cure, treat, or mitigate any disease in humans. Every package shall display the distinct specified "Ayurveda Aahar" logo prominently on the front-of-pack.
[relevance: ayurveda_aahar_nutraceutical]
""",
    ),
]


def run_sample_ingestion() -> None:
    """Convenience entrypoint to chunk and ingest the sample seed legal corpus."""
    pipeline = IngestionPipeline()
    results = pipeline.ingest_batch(SAMPLE_DOCUMENTS)
    for r in results:
        print(f"Ingested '{r['instrument_name']}': {r['chunks_count']} chunks, Qdrant synced: {r['qdrant_synced']}")


if __name__ == "__main__":
    run_sample_ingestion()
