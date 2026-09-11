# 🌿 IP-SAKTI Sahayak (आयुर्वेद बौद्धिक संपदा एवं नियामक एआई इंटेलिजेंस)

> **Authoritative, Citation-Grounded Statutory Intelligence for Ayurvedic Formulations, Phytopharmaceuticals, Botanical Patent Filings, and FSSAI Compliance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-000000.svg?logo=next.js)](https://nextjs.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20%7C%20Local%20LLM-black.svg)](https://ollama.com)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%82%E0%A4%A6%E0%A4%80-orange.svg)](#-bilingual-support-en--हिंदी)

---

## 📖 Executive Summary

**IP-SAKTI Sahayak** is an AI-powered regulatory intelligence and intellectual property guidance platform designed specifically for the Ayurvedic and botanical medicine domain. 

Unlike generic black-box LLMs that frequently hallucinate non-existent patent sections or outdated rules, Sahayak enforces a **Strict Zero-Hallucination Statutory Firewall**. Every answer is strictly grounded with verbatim citations from official Indian Acts, Central Gazette notifications, and First-Schedule classical Ayurvedic treatises.

---

## ✨ Key Capabilities

### 1. 🌿 Citation-Grounded Statutory Assistant
* **100% Gazette Grounded**: Direct section-level grounding across:
  * **The Patents Act, 1970**: § 3(p) (Traditional Knowledge bar), § 3(d) (Efficacy enhancement), § 3(e) (Synergism vs. mere admixture).
  * **The Biological Diversity Act, 2002 & 2023 Amendment**: § 3 (Foreign entity approvals), § 6 (Mandatory NBA Form III prior clearance).
  * **Drugs & Cosmetics Act, 1940 & Rules, 1945**: § 3(a) First-Schedule texts, § 3(h) P&P medicines, **Rule 122E (CDSCO 4-marker phytopharmaceutical standard)**.
  * **FSSAI (Ayurveda Aahar) Regulations, 2022**: Regulation 3 (Classical dietary preparations) & Regulation 5 (Prohibition of therapeutic disease cure claims).
* **Interactive Footnote Citations**: Clickable badges (`[1] ↗`, `[2] ↗`) open a slide-out drawer with official portal source verification (IP India, NBA, CDSCO, FSSAI).

### 2. 🛡️ Zero-Hallucination & Safe Abstention Firewall
* Employs deterministic citation validation: If even a single unretrieved or hallucinated citation token is detected, the **entire response is rejected**.
* If a question falls outside verified statutory scope or asks for speculative medical advice, the system gracefully presents an **Abstention Card** with structured legal reasoning and 1-click escalation to human facilitators.

### 3. 🔮 4-Step Formulation Classifier Wizard
* Guided multi-choice decision tree resolving regulatory pathways across **6 distinct formulation classes**:
  1. *Classical Generic Formulation* (First-Schedule texts, § 3(p) TK bar, $0 fee)
  2. *Patent or Proprietary Medicine (P&P)* (§ 3(h) DCA, § 3(e) synergism proof)
  3. *Phytopharmaceutical Drug* (Rule 122E, 4 bioactive markers, IND trials)
  4. *New Non-Classical Ayurvedic Drug* (Preclinical/clinical trial backed)
  5. *Ayurveda Aahar / Nutraceutical* (FSSAI 2022, no disease cure claims)
  6. *Ayurvedic Cosmetic (Saundarya Prasadak)* (BIS norms, topical care)

### 4. ⚖️ Dual-Regime Comparative Matrix
* Side-by-side legal matrix comparing Indian statutory laws with international frameworks:
  * **Indian Patents Act § 3(p)** vs. **TRIPS Art. 27.3(b)** & **WIPO GRATK Treaty (2024)**.
  * **NBA Access & Benefit Sharing (ABS)** vs. **Nagoya Protocol (CBD)**.
  * **CDSCO Rule 122E** vs. **US FDA Botanical Guidance** & **EMA Directive 2004/24/EC**.

### 5. 🇮🇳 Bilingual Support (EN + हिंदी)
* Complete localized interface, decision wizard, statutory citations, and legal summaries available in both English and Hindi.

### 6. 🎨 Organic Ayurvedic Design System
* Luxury editorial typography (**Cormorant Garamond**, **Playfair Display**, **Plus Jakarta Sans**).
* Natural floating botanical leaf animations and arched formulation showcase cards.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Next.js 16 Client (React 19 + Tailwind v4)           │
│  [Hero Landing] ── [RAG Assistant] ── [Classifier] ── [Comparator]    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON API
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Statutory Backend                       │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Hybrid Retrieval      │  │ Deterministic Decision Tree Engine    │  │
│  │ (Dense Vector + BM25) │  │ (4-Step Formulation Classifier)       │  │
│  └───────────┬───────────┘  └───────────────────────────────────────┘  │
│              ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Local LLM (Ollama / Qwen / LLaMA) + Zero-Hallucination Firewall  │  │
│  │ (Multi-turn retry loop & citation integrity validation)          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │   PostgreSQL / Supabase│      │   Qdrant Vector DB     │
       │   Relational Metadata, │      │   768-dim Dense Legal  │
       │   Logs & Gazette Text  │      │   Embeddings + Filters │
       └────────────────────────┘      └────────────────────────┘
```

---

## 🚀 Quickstart Guide

### Prerequisites
* **Python 3.11+**
* **Node.js 18+** & **npm**
* **Ollama** (for local LLM inference)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/vaibhavbariyar/Sahayak.git
cd Sahayak
```

---

### Step 2: Backend Setup
1. Navigate to `backend/` and create a virtual environment:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Start the FastAPI backend server:
   ```bash
   PYTHONPATH=.. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Backend will run at: [http://localhost:8000](http://localhost:8000)*  
   *API Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)*

---

### Step 3: Frontend Setup
1. In a new terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *Frontend will run at: [http://localhost:3000](http://localhost:3000)*

---

### Step 4: Ollama Local AI Setup
1. Install and start [Ollama](https://ollama.com):
   ```bash
   ollama serve
   ```
2. Pull the recommended lightweight local model:
   ```bash
   ollama pull qwen2.5:3b
   # or: ollama pull llama3.2:latest
   ```

---

## 🧪 Testing & Verification

Run the comprehensive unit, retrieval, classifier, and citation validation test suites:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

To run the empirical legal benchmark evaluation suite:
```bash
python scripts/empirical_test.py
```

---

## 📂 Project Structure

```
Sahayak/
├── backend/
│   ├── app/
│   │   ├── classifier/         # 4-step decision tree logic
│   │   ├── generation/         # Citation-constrained generation & firewall
│   │   ├── ingestion/          # Legal document chunker & sample seeds
│   │   ├── retrieval/          # BM25 + dense hybrid retrieval service
│   │   └── main.py             # FastAPI entrypoint & routes
│   ├── config/                 # Formulation categories & decision trees
│   ├── scripts/                # Empirical benchmark scripts
│   ├── tests/                  # Unit & integration test suites
│   ├── requirements.txt        # Python backend dependencies
│   └── .env.example            # Backend environment template
├── frontend/
│   ├── app/                    # Next.js App Router & global styles
│   ├── components/             # UI Components (Landing, Chat, Wizard, Cards)
│   ├── lib/                    # API client & translations (EN / HI)
│   ├── public/                 # High-resolution botanical assets & icons
│   └── package.json            # Frontend dependencies
├── schema_mvp.sql              # Supabase / PostgreSQL database schema
├── docker-compose.yml          # Qdrant vector database container
├── LICENSE                     # MIT License
└── README.md                   # Project documentation
```

---

## ⚖️ Statutory & Legal Disclaimer

*IP-SAKTI Sahayak is an educational and preliminary regulatory research tool designed to provide citation-grounded statutory information. It does not constitute formal legal advice. For formal patent applications, regulatory licensing, or commercial IP filings, consult a registered patent attorney or qualified AYUSH legal practitioner.*

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
