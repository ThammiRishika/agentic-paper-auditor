# Agentic Paper Auditor

A multi-agent system that autonomously scrapes an arXiv paper and executes a comprehensive **peer-review simulation**, producing a structured Judgement Report.

## Features

- 🔬 **Web Scraping**: Hybrid approach — arXiv API for metadata + Crawl4AI on `ar5iv.org` for full body
- ✂️ **Decomposition**: Splits the paper into sections (Abstract, Methodology, Results, Conclusion, etc.)
- 🤖 **6 Specialized Agents** powered by Gemini 1.5 Flash via `instructor`:
  - **Consistency Agent** — checks if methodology supports the claimed results
  - **Grammar Agent** — evaluates professional tone and syntax
  - **Novelty Agent** — searches Semantic Scholar to assess uniqueness
  - **Fact-Check Agent** — verifies constants, formulas, and numerical claims
  - **Authenticity Agent** — calculates a Fabrication Probability score
  - **Review Synthesizer** — converts all findings into a peer-review verdict
- 📄 **Judgement Report**: Markdown output with Executive Summary, scores, and detailed analysis
- 🖥️ **Streamlit UI**: Real-time agent progress + one-click report download

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd agentic-paper-auditor
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

The app supports **Gemini**, **Groq**, or **local** (LM Studio) — set `PROVIDER` and the corresponding API key in `.env`.

```bash
cp .env.example .env
# Edit .env: set PROVIDER (gemini | groq | local) and the matching API key(s)
```

```dotenv
# .env — choose one provider
PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Or: PROVIDER=groq + GROQ_API_KEY=...
# Or: PROVIDER=local (LM Studio at localhost:1234) + no API key
```

- **Gemini** : free tier at [aistudio.google.com](https://aistudio.google.com/app/apikey).
- **Groq**: free tier at [console.groq.com](https://console.groq.com/keys).
- **Local**: run [LM Studio](https://lmstudio.ai) with a model, then set `PROVIDER=local`.

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501`, paste an arXiv URL, and click **Analyze Paper**.

---

## Usage

1. Paste any arXiv URL (e.g. `https://arxiv.org/abs/1706.03762`)
2. Click **🚀 Analyze Paper**
3. Watch each agent run in real time
4. View the full Judgement Report in the **📄 Report** tab
5. Download the `.md` report for submission

Generated reports are also saved automatically to `outputs/`.

---

## Context & Token Management Strategy

This system enforces a strict **≤ 16k tokens per LLM call** budget throughout the pipeline.

### 1. Section-Level Context Isolation _(Primary Strategy)_

The Section Decomposer splits the full paper into named sections upfront. Each agent receives only the 2–3 sections it actually needs — not the full paper. This is the primary mechanism; chunking is a fallback.

### 2. Tightened Summarization Prompt

When a section exceeds ~12k tokens, `summarize_if_too_long()` compresses it chunk-by-chunk using a prompt that explicitly instructs the LLM:

> _"Do NOT drop formulas, key numerical results, statistical values, or unusual edge cases. Preserve all quantitative claims exactly as stated."_

### 3. Claims Cap _(Fact-Check Agent)_

Extracted claims are capped at **top 20 most important**, prioritising claims most central to the paper's conclusions. Prevents excessive verification calls while targeting the highest-value checks.

### 4. Rolling Context _(Authenticity Agent)_

Runs 3 passes over the paper. Each pass explicitly carries the previous pass's `reasoning` field as prompt context — maintaining analytical continuity without relying on LLM memory.

### 5. Multi-Pass Synthesis _(Consistency Agent)_

Methodology and Results are each summarised independently, then combined in a single consistency check call — every LLM call stays within budget.

---

## Project Structure

```
agentic-paper-auditor/
├── app.py                    # Streamlit UI
├── requirements.txt
├── .env.example
├── models/                   # Pydantic output models
│   ├── consistency.py
│   ├── grammar.py
│   ├── novelty.py
│   ├── factcheck.py          # ClaimsOnly + Claim + FactCheckResult
│   ├── authenticity.py
│   └── verdict.py            # PeerReviewVerdict
├── scraper/                  # arXiv API + Crawl4AI
├── decomposer/               # Section splitter
├── agents/                   # 6 specialized agents
├── tools/                    # Semantic Scholar API wrapper
├── pipeline/                 # Orchestrator
├── report/                   # Markdown report generator
└── outputs/                  # Generated reports
```

---

## Requirements

- Python 3.11+
- One of: **Gemini** (free), **Groq** (free), or **local** LM Studio — see Setup step 3.
- No other paid API keys needed — Semantic Scholar is free and keyless.
