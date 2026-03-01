from agents.base_agent import extract_structured
from models.authenticity import AuthenticityResult


def run_authenticity(sections: dict, paper: dict | None = None) -> AuthenticityResult:
    """
    Rolling-summary strategy (3 passes):
      Pass 1: Abstract + Introduction  → partial_findings_1
      Pass 2: Methodology + Results, carrying Pass 1 context forward
      Pass 3: Conclusion, carrying Pass 2 context → final AuthenticityResult

    Each pass explicitly receives prior findings in the prompt to maintain
    analytical continuity without relying on LLM memory (stateless calls).
    """
    abstract = sections.get("Abstract", "")[:4_000]
    introduction = sections.get("Introduction", "")[:4_000]
    methodology = sections.get("Methodology", sections.get("Method", ""))[:8_000]
    results = sections.get("Results", sections.get("Experiments", ""))[:8_000]
    conclusion = sections.get("Conclusion", "")[:4_000]

    title = paper.get("title", "") if paper else ""
    arxiv_id = paper.get("arxiv_id", "") if paper else ""
    categories = ", ".join(paper.get("categories", [])) if paper else ""

    meta_header = f"Paper: {title} (arXiv:{arxiv_id}) in categories [{categories}]" if title or arxiv_id else ""

    # ── Pass 1 ──────────────────────────────────────────────────────────────
    p1: AuthenticityResult = extract_structured(
        f"""You are a senior peer reviewer assessing the authenticity and integrity of a research paper.
{meta_header}

Be conservative: most peer-reviewed or arXiv-style research papers are NOT fabricated.
Assign "High" risk or fabrication_probability above 80% ONLY if there are clear signs of fraud,
such as impossible numerical results, blatant contradictions, or nonsensical experimental design.
Do NOT label a paper as likely fabricated just because results are strong or surprising.

Analyse the following sections for signs of fabrication, statistical anomalies, or logical inconsistencies.

ABSTRACT:
{abstract}

INTRODUCTION:
{introduction}

Provide an initial fabrication risk assessment. Your findings will be refined in subsequent passes.""",
        AuthenticityResult,
    )

    # ── Pass 2 (carries Pass 1 context) ─────────────────────────────────────
    p2: AuthenticityResult = extract_structured(
        f"""You are continuing a peer-review authenticity assessment.

{meta_header}

PREVIOUS FINDINGS (Pass 1):
{p1.reasoning}
Risk so far: {p1.risk_level} ({p1.fabrication_probability:.1f}%)
Red flags so far: {", ".join(p1.red_flags) or "None"}

Now analyse the Methodology and Results sections for additional fabrication signals,
suspicious statistical patterns, or unsupported claims.

Be cautious: only upgrade the risk to "High" if you see strong evidence of fabrication,
such as inconsistent numbers across sections, impossible accuracies, or clearly made-up experiments.

METHODOLOGY:
{methodology}

RESULTS:
{results}

Update your assessment incorporating both Pass 1 findings and these new observations.""",
        AuthenticityResult,
    )

    # ── Pass 3 (final score, carries Pass 2 context) ─────────────────────────
    p3: AuthenticityResult = extract_structured(
        f"""You are completing a peer-review authenticity assessment.

{meta_header}

CUMULATIVE FINDINGS SO FAR (Passes 1 & 2):
{p2.reasoning}
Risk so far: {p2.risk_level} ({p2.fabrication_probability:.1f}%)
Red flags so far: {", ".join(p2.red_flags) or "None"}

Now review the Conclusion and provide your final fabrication probability score.
Consider whether the conclusion makes claims beyond what the results support.

Again, be conservative:
- Use "High" risk or fabrication_probability above 80% ONLY when there is compelling evidence
  of fabrication or severe misrepresentation.
- If the paper is a widely cited or foundational-looking work with plausible experiments and
  no glaring contradictions, prefer "Low" or "Medium" risk.

CONCLUSION:
{conclusion}

Return your FINAL AuthenticityResult with the definitive fabrication_probability, risk_level,
full reasoning, and complete list of red flags.""",
        AuthenticityResult,
    )

    return p3
