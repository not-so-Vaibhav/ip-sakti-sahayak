# UI/UX Design Document: IP-SAKTI Sahayak

**Companion to:** IP-SAKTI-Sahayak-PRD.md, IP-SAKTI-Sahayak-TRD.md
**Scope:** Stage 1 (Hackathon MVP) interface design

---

## 1. Purpose

This document specifies the interface a user actually interacts with —
screens, flows, and components — implementing the functional requirements in
the PRD through a design that keeps a legally complex tool usable by someone
who is not a lawyer.

---

## 2. Design Principles

1. **Never hide where an answer came from.** Every claim is visibly tied to a
   source. This isn't a "nice to have" panel — it's the product's core trust
   mechanism, so it must be as prominent as the answer itself, not tucked
   into a collapsed footnote.
2. **Show confidence, don't just imply it.** A visible confidence signal on
   every answer, and a genuinely different visual state when the system
   abstains — abstention should look and feel distinct from "here's your
   answer," never a smaller version of the same thing.
3. **Classify before you answer.** The formulation-classification flow is a
   real step the user goes through, not a hidden backend decision — because
   the result changes what the rest of the tool tells them.
4. **Jurisdiction is a mode, not a filter buried in settings.** National vs.
   International is a first-class, always-visible toggle — switching it
   should visibly change the answer, so the user never wonders which regime
   they're reading.
5. **Bilingual parity.** Hindi is not a translated afterthought bolted onto
   an English-first design — layout, type, and information density need to
   work equally in both from the start.
6. **Plain language, cited precision.** Explanations are written for a
   non-lawyer; citations remain exact and unsimplified underneath.

---

## 3. End-to-End User Flow

```
 Landing
   │
   ▼
 Language select (EN / HI) ──────────────────────────────┐
   │                                                       │
   ▼                                                       │
 "What are you asking about?"                              │
   │                                                       │
   ├── I have a specific formulation/product ──► Classifier flow (Sec 5.2)
   │                                                   │
   │                                                   ▼
   │                                          Formulation category assigned
   │                                                   │
   └── I have a general IP/regulatory question ───────┤
                                                        ▼
                                          Jurisdiction toggle: India / International
                                                        │
                                                        ▼
                                               Chat / Query interface
                                                        │
                                       ┌────────────────┴────────────────┐
                                       ▼                                 ▼
                            Confident answer + citations         Abstain + escalate
                                       │                                 │
                                       ▼                                 ▼
                            Source viewer (clause detail)      Human facilitator handoff
```

---

## 4. Information Architecture

```
Home
├── Formulation Classifier          (guided Q&A → category + explanation)
├── Ask a Question                  (main chat interface)
│   ├── Jurisdiction toggle (India / International)
│   ├── Language switch (EN / हिंदी)
│   ├── Answer + citation list
│   ├── Source viewer (side panel / modal)
│   └── Regime Comparator            (side-by-side India vs. International)
├── ABS Compliance Helper            (surfaced contextually, also directly reachable)
├── TKDL & Precedent Reference        (Turmeric/Neem case library, TKDL info)
└── Escalate to Human Facilitator     (always reachable, not just on abstention)
```

---

## 5. Key Screens

### 5.1 Landing / Language Select

```
┌──────────────────────────────────────────────────────┐
│  IP-SAKTI Sahayak                                       │
│  Ayurveda IP & Regulatory Guidance — cited, bilingual   │
│                                                          │
│   [ English ]     [ हिंदी ]                             │
│                                                          │
│   ⓘ This tool provides information, not legal advice.   │
│                                                          │
│   [ I have a specific product/formulation ]              │
│   [ I have a general question ]                          │
└──────────────────────────────────────────────────────┘
```
The disclaimer is on the landing screen, not just buried in a terms page —
per PRD FR9, it needs to be a standing, visible element.

### 5.2 Formulation Classifier (guided flow)

One question per screen, plain language, with a visible progress indicator
and a plain-language explanation of *why* the question matters.

```
┌──────────────────────────────────────────────────────┐
│  Step 2 of 4                                    ● ● ○ ○ │
│                                                          │
│  Does your formulation come directly from a             │
│  recognized classical text (e.g. Charaka Samhita),       │
│  unchanged?                                              │
│                                                          │
│  [ Yes, unchanged ]     [ No / I've modified it ]        │
│                                                          │
│  Why we're asking: this determines whether your          │
│  product is treated as traditional knowledge or as       │
│  a new formulation — they have very different patent      │
│  and licensing paths.                                     │
└──────────────────────────────────────────────────────┘
```

**Result screen:**

```
┌──────────────────────────────────────────────────────┐
│  Your formulation is classified as:                     │
│                                                          │
│  ▶ Classical / Generic Medicine                          │
│                                                          │
│  What this means:                                        │
│  • Treated as traditional knowledge — cannot be newly     │
│    patented (Patents Act, Sec. 3(p))                       │
│  • Defended against foreign misappropriation via TKDL      │
│  • No clinical trial requirement to market as classical    │
│                                                          │
│  [ Ask a question about this category ]                   │
│  [ Redo classification ]                                   │
└──────────────────────────────────────────────────────┘
```

### 5.3 Main Chat / Query Interface

```
┌──────────────────────────────────────────────────────┐
│  Jurisdiction: [ ● India ] [ ○ International ]  हिंदी/EN │
├──────────────────────────────────────────────────────┤
│                                                          │
│  You: Can I patent a turmeric-based wound-healing paste? │
│                                                          │
│  IP-SAKTI:                                                │
│  No — a plain turmeric-based formulation is treated as    │
│  traditional knowledge and falls under the patent bar      │
│  in Section 3(p) of the Patents Act.[1] It may still be    │
│  eligible for other protection depending on how it's        │
│  processed or combined — would you like to check that?     │
│                                                          │
│  Confidence: ●●●●○  High           [1] Patents Act, 1970,  │
│                                          Sec. 3(p) ↗         │
├──────────────────────────────────────────────────────┤
│  [ Type your question...                    ] [ Send ]   │
└──────────────────────────────────────────────────────┘
```

The citation `[1]` is always clickable — clicking opens the source viewer
(5.4), never just a plain footnote.

### 5.4 Source Viewer (clause detail)

```
┌──────────────────────────────────────────────────────┐
│  ✕  Patents Act, 1970 — Section 3(p)                     │
├──────────────────────────────────────────────────────┤
│  "The following are not inventions... (p) an invention    │
│  which, in effect, is traditional knowledge or which is    │
│  an aggregation or duplication of known properties of      │
│  traditionally known component or components."             │
│                                                          │
│  Instrument: The Patents Act, 1970                        │
│  Last amended: 01-08-2024                                  │
│  Source: ipindia.gov.in ↗ (official)                       │
└──────────────────────────────────────────────────────┘
```
This is the literal implementation of "cite-or-refuse" as a UI object, not
just a backend rule — the user should be able to verify every claim without
leaving the app.

### 5.5 Abstention / Escalation State

This must look **visually distinct** from a normal answer — not a smaller or
grayed-out version of the same card.

```
┌──────────────────────────────────────────────────────┐
│  ⚠ I don't have a confidently-sourced answer for this.   │
│                                                          │
│  This question may need a qualified IP professional's     │
│  review — I'd rather say that than guess.                  │
│                                                          │
│  [ Talk to a human IP facilitator ]                        │
│  [ Rephrase my question ]                                   │
└──────────────────────────────────────────────────────┘
```

### 5.6 Regime Comparator (differentiator feature)

```
┌──────────────────────────────────────────────────────┐
│  Comparing: Traditional Knowledge Patent Protection        │
├───────────────────────┬──────────────────────────────┤
│  India                 │  International                  │
├───────────────────────┼──────────────────────────────┤
│  Patents Act Sec. 3(p) │  TRIPS Art. 27.3(b)              │
│  bars TK patenting     │  allows sui generis TK regimes    │
│                        │  at national discretion            │
│                        │                                  │
│  Defended via TKDL     │  WIPO GRATK Treaty (2024) requires │
│  prior art             │  disclosure of TK/GR origin in      │
│                        │  patent filings                     │
└───────────────────────┴──────────────────────────────┘
```

---

## 6. Component Library / Visual Design

Colors carried over from the pitch deck for consistency across all
hackathon deliverables:

| Token | Hex | Use |
|---|---|---|
| Primary (navy) | `#1F497D` | Headers, primary text emphasis |
| Accent (blue) | `#0070C0` | Interactive elements, links, active toggle state |
| Confidence — high | `#3C9A5F` (green) | ●●●●○ style indicator, 4–5 dots |
| Confidence — medium | `#D9A02B` (amber) | 2–3 dots |
| Confidence — low / abstain | `#C0504D` (red, matches theme accent2) | Abstention state border/icon |
| Background | `#FFFFFF` | Base |
| Source-viewer panel | `#EEECE1` (theme lt2) | Distinguish from main chat background |

Typography: sans-serif throughout (matches deck's Arial), legal quoted text
in a monospace or serif variant inside the source viewer only, to visually
separate "our explanation" from "the actual legal text."

**Confidence indicator component:** a 5-dot scale, always paired with a text
label ("High"/"Medium"/"Low") — never color alone, since color-only signals
fail accessibility and fail in grayscale printouts of the deck.

---

## 7. Content & Tone Guidelines

- Plain-language explanations always precede or accompany the citation, never
  replace it — the user gets both "what this means" and "what it actually says"
- The "information, not legal advice" disclaimer appears: on landing, in the
  chat interface footer, and again on the escalation screen — repetition here
  is intentional, not redundant
- Classification and comparator outputs use short, scannable bullets, not
  paragraphs — this is a lookup tool, not a reading experience
- Hindi content is written natively for tone, not machine-translated verbatim
  from the English copy where idiom matters (disclaimers, category names)

---

## 8. Accessibility

- Confidence signal uses shape/count + color + text label together (not
  color alone)
- All interactive elements (toggle, citation links, escalation buttons)
  keyboard-navigable
- Source viewer text meets standard contrast ratios against its panel
  background
- Screen-reader labels for the jurisdiction toggle and language switch state
  changes (announce "Jurisdiction: India" / "जुरिस्डिक्शन: भारत" on toggle)

---

## 9. Responsive / Mobile Considerations

- Source viewer becomes a full-screen modal on mobile rather than a side
  panel (no room for both chat and side-by-side clause view)
- Regime Comparator stacks vertically (India above International) on narrow
  screens rather than side-by-side columns
- Classifier flow's one-question-per-screen pattern is inherently mobile-
  friendly already — no redesign needed there

---

## 10. Edge Cases & Error States

| Situation | UI behavior |
|---|---|
| Corpus has no matching source at all | Abstention state (5.5), not a generic error |
| User asks a medical/efficacy question (out of scope) | Distinct message: "This is an IP/regulatory tool, not a medical guidance tool" — not treated as low confidence, treated as explicitly out of scope |
| Jurisdiction toggle switched mid-conversation | Previous answers stay visible but visually tagged with their original jurisdiction; new queries use the new toggle state |
| Classifier answer changed / redone | Old classification-dependent answers get a subtle "based on previous classification" tag rather than silently updating |

---

## 11. Usability Validation Plan (ties to PRD Section 11 test plan)

Before the demo, walk at least one person unfamiliar with the project through:
1. Landing → classifier → first question → citation click-through
2. A deliberately out-of-scope question → confirm the abstention state reads
   as trustworthy, not broken
3. Jurisdiction toggle switch mid-session → confirm it's clear which regime
   the current answer belongs to

If a first-time user gets confused at any of these three points, that's a UI
problem to fix before judging, not a minor polish item — these are exactly
the moments a judge is likely to probe.
