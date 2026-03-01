import os
from datetime import datetime
from pathlib import Path

from models.consistency import ConsistencyResult
from models.grammar import GrammarResult
from models.novelty import NoveltyResult
from models.factcheck import FactCheckResult
from models.authenticity import AuthenticityResult
from models.verdict import PeerReviewVerdict

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def _fact_check_table(fc: FactCheckResult) -> str:
    if not fc.fact_check_log:
        return "_No claims extracted._"
    rows = ["| # | Claim | Status | Source |", "|---|-------|--------|--------|"]
    for i, c in enumerate(fc.fact_check_log, 1):
        status_emoji = {"verified": "✅", "unverified": "⚠️", "incorrect": "❌"}.get(c.status, "")
        source = c.source or "—"
        rows.append(f"| {i} | {c.claim} | {status_emoji} {c.status} | {source} |")
    return "\n".join(rows)


def _red_flags(auth: AuthenticityResult) -> str:
    if not auth.red_flags:
        return "_No red flags identified._"
    return "\n".join(f"- {flag}" for flag in auth.red_flags)


def _contradictions(c: ConsistencyResult) -> str:
    if not c.contradictions:
        return "_No contradictions identified._"
    return "\n".join(
        f"- **{cont.location}**: {cont.description}" for cont in c.contradictions
    )


def _grammar_issues(g: GrammarResult) -> str:
    if not g.issues:
        return "_No significant grammar issues found._"
    return "\n".join(f'- "{issue.excerpt}" — {issue.issue}' for issue in g.issues)


def _related_papers(n: NoveltyResult) -> str:
    if not n.related_papers:
        return "_No closely related papers found._"
    lines = []
    for p in n.related_papers:
        year = f" ({p.year})" if p.year else ""
        lines.append(f"- **{p.title}**{year} — {p.authors}  \n  _{p.similarity}_")
    return "\n".join(lines)


def generate_report(data: dict) -> str:
    paper: dict = data["paper"]
    r = data["results"]

    c: ConsistencyResult  = r["consistency"]
    g: GrammarResult      = r["grammar"]
    n: NoveltyResult      = r["novelty"]
    f: FactCheckResult    = r["fact_check"]
    a: AuthenticityResult = r["authenticity"]
    v: PeerReviewVerdict  = r["verdict"]

    rec_emoji = {
        "Accept": "✅",
        "Minor Revision": "🟡",
        "Major Revision": "🟠",
        "Reject": "❌",
    }.get(v.recommendation, "")

    report = f"""# Judgement Report — {paper['title']}

> **Generated**: {datetime.now():%Y-%m-%d %H:%M}  |  **arXiv ID**: `{paper['arxiv_id']}`  |  **Authors**: {paper['authors']}

---

## Executive Summary

| | |
|---|---|
| **Recommendation** | {rec_emoji} **{v.recommendation}** |
| **Confidence** | {v.confidence:.0%} |
| **Fabrication Risk** | **{a.risk_level}** ({a.fabrication_probability:.1f}%) |
| **Overall Consistency** | **{c.consistency_score} / 100** |

{v.justification}

---

## Scores at a Glance

| Metric | Score |
|--------|-------|
| Consistency | {c.consistency_score} / 100 |
| Grammar | {g.grammar_rating} |
| Novelty Index | {n.novelty_index} |
| Fact Check | ✅ {f.verified_count} verified · ⚠️ {f.unverified_count} unverified · ❌ {f.incorrect_count} incorrect |
| Fabrication Probability | {a.fabrication_probability:.1f}% ({a.risk_level} Risk) |

---

## Detailed Analysis

### 1. Consistency

**Score: {c.consistency_score} / 100**

{c.reasoning}

**Contradictions Found:**

{_contradictions(c)}

---

### 2. Grammar & Language

**Rating: {g.grammar_rating}**

{g.reasoning}

**Issues Identified:**

{_grammar_issues(g)}

---

### 3. Novelty

**Novelty Index: {n.novelty_index}**

{n.reasoning}

**Related Papers Found:**

{_related_papers(n)}

---

### 4. Fact-Check Log

**{f.verified_count} verified · {f.unverified_count} unverified · {f.incorrect_count} incorrect**

{_fact_check_table(f)}

---

### 5. Authenticity / Fabrication Assessment

**Fabrication Probability: {a.fabrication_probability:.1f}% ({a.risk_level} Risk)**

{a.reasoning}

**Red Flags:**

{_red_flags(a)}

---

## Metadata

| Field | Value |
|-------|-------|
| arXiv ID | `{paper['arxiv_id']}` |
| Authors | {paper['authors']} |
| Submitted | {paper.get('published', 'N/A')} |
| Categories | {', '.join(paper.get('categories', [])) or 'N/A'} |
| Sections Detected | {', '.join(data.get('sections', []))} |
"""
    return report


def save_report(report_md: str, arxiv_id: str) -> Path:
    """Write the report to outputs/ and return the file path."""
    safe_id = arxiv_id.replace("/", "_")
    path = OUTPUT_DIR / f"judgement_report_{safe_id}.md"
    path.write_text(report_md, encoding="utf-8")
    return path
