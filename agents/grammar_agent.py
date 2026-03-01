from agents.base_agent import extract_structured
from models.grammar import GrammarResult


def run_grammar(sections: dict) -> GrammarResult:
    """
    Single-pass strategy: Abstract + Introduction are always short enough.
    Evaluates professional tone, grammar, clarity, and syntax.
    """
    abstract     = sections.get("Abstract", "")
    introduction = sections.get("Introduction", "")

    # Combine and cap — these sections rarely exceed 8k tokens combined
    text = (abstract + "\n\n" + introduction)[:12_000]

    prompt = f"""You are a professional academic editor reviewing a research paper.

Evaluate the grammar, syntax, professional tone, and clarity of the following text.
Identify specific issues if any, and rate the overall language quality.

TEXT:
{text}

Return a GrammarResult with:
- grammar_rating: "High", "Medium", or "Low"
- issues: list of specific grammar/language problems found (empty if quality is High)
- reasoning: brief overall assessment of language quality and tone
"""
    return extract_structured(prompt, GrammarResult)
