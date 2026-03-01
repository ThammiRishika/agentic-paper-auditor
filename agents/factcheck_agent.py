from agents.base_agent import extract_structured, summarize_if_too_long
from models.factcheck import ClaimsOnly, Claim, FactCheckResult


def run_factcheck(sections: dict) -> FactCheckResult:
    """
    Two-pass strategy:
      Pass 1: Extract top-20 most important factual claims (ClaimsOnly model).
      Pass 2+: Verify claims in batches of 5 (FactCheckResult model per batch).
    """
    results_text = (
        sections.get("Results", "")
        or sections.get("Experiments", "")
        or sections.get("Evaluation", "")
    )
    abstract_text = sections.get("Abstract", "")

    # Combine and cap — abstract gives the model anchoring context
    combined = (abstract_text + "\n\n" + results_text)[:24_000]
    combined = summarize_if_too_long(combined, max_tokens=6_000)

    # Pass 1: Extract claims 
    claims = _extract_claims(combined)

    # Retry with simpler prompt if model returned empty list
    if not claims:
        claims = _extract_claims_simple(
            sections.get("Abstract", "")[:4_000] or combined[:4_000]
        )

    if not claims:
        return FactCheckResult(
            fact_check_log=[],
            verified_count=0,
            unverified_count=0,
            incorrect_count=0,
        )

    claims = claims[:20]  # hard cap

    # Pass 2+: Verify in batches of 5 
    verified_claims: list[Claim] = []
    for i in range(0, len(claims), 5):
        batch = claims[i : i + 5]
        batch_text = "\n".join(f"{j+1}. {c}" for j, c in enumerate(batch))
        verify_prompt = f"""Verify each claim below using well-established scientific knowledge and published research.

For each claim:
- Use "verified" only if it clearly matches well-known, well-documented results.
- Use "incorrect" ONLY if it clearly contradicts well-established facts or published benchmarks.
- If you are uncertain, or if evidence is mixed or depends on context, use "unverified" (do NOT guess "incorrect").

Return for each claim: status (verified/unverified/incorrect), a source if available, and a brief note.

CLAIMS:
{batch_text}
"""
        batch_result: FactCheckResult = extract_structured(verify_prompt, FactCheckResult)
        verified_claims.extend(batch_result.fact_check_log)

    return FactCheckResult(
        fact_check_log=verified_claims,
        verified_count=sum(1 for c in verified_claims if c.status == "verified"),
        unverified_count=sum(1 for c in verified_claims if c.status == "unverified"),
        incorrect_count=sum(1 for c in verified_claims if c.status == "incorrect"),
    )


def _extract_claims(text: str) -> list[str]:
    """Primary extraction — asks for top 20 most important verifiable claims."""
    prompt = f"""From the research paper text below, list the TOP 20 most important factual claims.
Focus on: numerical results, benchmark scores, statistics, formulas, comparisons to prior work.
Return only a list of concise claims, one per item.

TEXT:
{text}
"""
    extracted: ClaimsOnly = extract_structured(prompt, ClaimsOnly)
    return extracted.claims or []


def _extract_claims_simple(text: str) -> list[str]:
    """Simpler fallback prompt for models that struggle with the primary extraction."""
    prompt = f"""List 10 factual statements from this text that could be verified (numbers, scores, comparisons):

{text}

Return as a list of short factual claims.
"""
    extracted: ClaimsOnly = extract_structured(prompt, ClaimsOnly)
    return extracted.claims or []
