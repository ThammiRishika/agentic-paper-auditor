from agents.base_agent import extract_structured, summarize_if_too_long
from models.consistency import ConsistencyResult


def _fallback_methodology(sections: dict) -> str:
    """Heuristic methodology section when explicit 'Methodology/Method' is absent."""
    method_like = []
    for name, text in sections.items():
        lower = name.lower()
        if any(
            key in lower
            for key in [
                "methodology",
                "method",
                "approach",
                "model",
                "architecture",
                "framework",
                "implementation",
                "residual learning",
                "identity mapping",
                "network architectures",
            ]
        ):
            method_like.append(text)
    return "\n\n".join(method_like)


def _fallback_results(sections: dict) -> str:
    """Heuristic results section when explicit 'Results/Experiments' is absent."""
    result_like = []
    for name, text in sections.items():
        lower = name.lower()
        if any(
            key in lower
            for key in [
                "results",
                "experiments",
                "evaluation",
                "analysis",
                "classification",
                "imagenet",
                "cifar",
                "detection",
            ]
        ):
            result_like.append(text)
    return "\n\n".join(result_like)


def run_consistency(sections: dict) -> ConsistencyResult:
    """
    Multi-pass strategy:
      Pass 1: Summarize Methodology (if too long)
      Pass 2: Summarize Results (if too long)
      Pass 3: Consistency check using both summaries + Conclusion
    Each pass stays ≤ 16k tokens.
    """
    methodology_raw = sections.get("Methodology") or sections.get("Method")
    results_raw = sections.get("Results") or sections.get("Experiments")

    if not methodology_raw:
        methodology_raw = _fallback_methodology(sections)
    if not results_raw:
        results_raw = _fallback_results(sections)

    methodology = summarize_if_too_long(methodology_raw)
    results = summarize_if_too_long(results_raw)
    conclusion = sections.get("Conclusion", "")[:8_000]

    # If we still have almost no structured separation, fall back to a global view.
    if not methodology.strip() and not results.strip():
        combined = "\n\n".join(sections.values())
        combined = summarize_if_too_long(combined)
        prompt = f"""You are a scientific peer reviewer evaluating the internal consistency of a research paper.

The paper's sections could not be cleanly separated into 'Methodology' and 'Results'. Instead, you are given
a combined summary of the available content. Assess whether the claims made appear to be supported by the
described methods and evidence, and whether there are obvious logical contradictions.

PAPER SUMMARY:
{combined}

Return a ConsistencyResult with:
- consistency_score: integer 0–100 (100 = perfectly consistent)
- contradictions: list of any contradictions found (empty if none)
- reasoning: brief explanation of the score
"""
        return extract_structured(prompt, ConsistencyResult)

    prompt = f"""You are a scientific peer reviewer evaluating the internal consistency of a research paper.

Evaluate whether the methodology logically supports the claimed results, and whether the conclusion
accurately reflects the findings. Identify any contradictions, unsupported claims, or logical leaps.

METHODOLOGY SUMMARY:
{methodology}

RESULTS SUMMARY:
{results}

CONCLUSION:
{conclusion}

Return a ConsistencyResult with:
- consistency_score: integer 0–100 (100 = perfectly consistent)
- contradictions: list of any contradictions found (empty if none)
- reasoning: brief explanation of the score
"""
    return extract_structured(prompt, ConsistencyResult)
