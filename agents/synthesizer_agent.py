from agents.base_agent import extract_structured
from models.consistency import ConsistencyResult
from models.grammar import GrammarResult
from models.novelty import NoveltyResult
from models.factcheck import FactCheckResult
from models.authenticity import AuthenticityResult
from models.verdict import PeerReviewVerdict


def run_synthesizer(
    consistency: ConsistencyResult,
    grammar: GrammarResult,
    novelty: NoveltyResult,
    factcheck: FactCheckResult,
    authenticity: AuthenticityResult,
) -> PeerReviewVerdict:
    """
    Final agent — converts specialist analysis outputs into a peer-review verdict.
    Receives a compact digest of all five agent scores (well within 16k tokens).
    """
    red_flags_text = (
        "\n  - ".join(authenticity.red_flags) if authenticity.red_flags else "None identified"
    )

    contradictions_text = (
        "\n  - ".join(
            f"{c.location}: {c.description}" for c in consistency.contradictions
        )
        if consistency.contradictions
        else "None identified"
    )

    prompt = f"""You are a senior academic peer reviewer making a final recommendation.
Based on the specialist analysis reports below, provide a comprehensive peer-review verdict.

━━ SPECIALIST REPORT DIGEST ━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSISTENCY ANALYSIS
  Score: {consistency.consistency_score}/100
  Contradictions found:
  - {contradictions_text}
  Reasoning: {consistency.reasoning}

GRAMMAR & LANGUAGE
  Rating: {grammar.grammar_rating}
  Reasoning: {grammar.reasoning}

NOVELTY ASSESSMENT
  Novelty Index: {novelty.novelty_index}
  Related papers found: {len(novelty.related_papers)}
  Reasoning: {novelty.reasoning}

FACT-CHECK RESULTS
  Verified claims: {factcheck.verified_count}
  Unverified claims: {factcheck.unverified_count}
  Incorrect claims: {factcheck.incorrect_count}

AUTHENTICITY / FABRICATION RISK
  Fabrication Probability: {authenticity.fabrication_probability:.1f}%
  Risk Level: {authenticity.risk_level}
  Red Flags:
  - {red_flags_text}
  Reasoning: {authenticity.reasoning}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on the above, provide your peer-review recommendation:
- "Accept": publication-ready, strong contributions, no major issues
- "Minor Revision": good paper, needs small fixes
- "Major Revision": significant concerns requiring substantial rework
- "Reject": fundamental flaws, fabrication risk too high, or insufficient novelty

Return a PeerReviewVerdict with your recommendation, confidence (0.0–1.0), and a one-paragraph
justification that synthesises all the above findings.
"""
    return extract_structured(prompt, PeerReviewVerdict)
