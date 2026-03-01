import re

# ── Heading detection (regex only, zero cost) ─────────────────────────────────

_ANY_HEADING_RE = re.compile(r"(?im)^#{1,4}\s+(.+)$")

_KNOWN_KWORDS = [
    "abstract", "introduction", "related work", "background",
    "preliminaries", "methodology", "method", "approach", "model",
    "architecture", "framework", "results", "experiments", "evaluation",
    "analysis", "discussion", "conclusion", "future work",
]
_NUMBERED_RE = re.compile(
    r"(?im)^\d{1,2}\.?\s+("
    + "|".join(re.escape(s) for s in _KNOWN_KWORDS)
    + r")\b[^\n]*$"
)
_CAPS_RE = re.compile(
    r"(?im)^("
    + "|".join(re.escape(s.upper()) for s in _KNOWN_KWORDS)
    + r")\s*$"
)

_LEADING_NUM_RE = re.compile(r"^\d[\d.]*\s*")

_JUNK_WORDS = {
    "references", "acknowledgements", "acknowledgments", "acknowledgement",
    "appendix", "bibliography", "supplementary", "supplemental",
    "notation", "proofs", "proof",
}

# ── Canonical word-scan map ───────────────────────────────────────────────────
# Scans ALL words in a section name — handles arbitrary titles like
# "Deep Residual Learning" (word "learning" → Methodology),
# "ImageNet Classification" (word "classification" → Experiments).
# Words are checked in priority order: first match wins.
_WORD_TO_CANONICAL = {
    # Introduction
    "introduction": "Introduction",
    # Related Work / Background
    "related":       "Related Work",
    "background":    "Background",
    "preliminaries": "Background",
    "preliminary":   "Background",
    # Methodology (covers any section describing HOW the system works)
    "methodology":   "Methodology",
    "method":        "Methodology",
    "methods":       "Methodology",
    "approach":      "Methodology",
    "framework":     "Methodology",
    "model":         "Methodology",
    "architecture":  "Methodology",
    "network":       "Methodology",
    "learning":      "Methodology",   # "Deep Residual Learning"
    "attention":     "Methodology",   # "Multi-Head Attention"
    "transformer":   "Methodology",
    "implementation":"Methodology",
    "design":        "Methodology",
    "training":      "Methodology",
    "formulation":   "Methodology",
    "mapping":       "Methodology",   # "Identity Mapping By Shortcuts"
    "shortcut":      "Methodology",
    # Experiments / Results (covers any evaluation section)
    "results":       "Results",
    "experiments":   "Experiments",
    "experiment":    "Experiments",
    "evaluation":    "Experiments",
    "analysis":      "Experiments",
    "ablation":      "Experiments",
    "performance":   "Experiments",
    "benchmark":     "Experiments",
    "comparison":    "Experiments",
    "imagenet":      "Experiments",
    "cifar":         "Experiments",
    "detection":     "Experiments",
    "classification":"Experiments",
    "recognition":   "Experiments",
    "translation":   "Experiments",
    "generation":    "Experiments",
    "pascal":        "Experiments",
    "coco":          "Experiments",
    "filters":       "Experiments",
    # Discussion
    "discussion":    "Discussion",
    "limitations":   "Discussion",
    # Conclusion
    "conclusion":    "Conclusion",
    "conclusions":   "Conclusion",
    "summary":       "Conclusion",
    "future":        "Conclusion",
}


def _clean_name(raw: str) -> str:
    return _LEADING_NUM_RE.sub("", raw).strip().title()


def _is_junk(name: str) -> bool:
    words = name.lower().split()
    return bool(words) and words[0] in _JUNK_WORDS


def _is_table_header(raw: str) -> bool:
    return "|" in raw


def _to_canonical(name: str) -> str:
    """
    Scan all words in the section name against _WORD_TO_CANONICAL.
    Returns the first canonical match, or the original name if none found.
    """
    words = name.lower().replace("-", " ").split()
    for word in words:
        if word in _WORD_TO_CANONICAL:
            return _WORD_TO_CANONICAL[word]
    return name   # keep original if no mapping found


def _find_all_headings(text: str) -> list:
    matches = []
    for pattern in [_ANY_HEADING_RE, _NUMBERED_RE, _CAPS_RE]:
        for m in pattern.finditer(text):
            raw = m.group(1) if m.lastindex else m.group(0)
            if _is_table_header(raw):
                continue
            # Skip paper title: very long heading in first 200 chars
            if m.start() < 200 and len(raw) > 50:
                continue
            matches.append(m)

    matches.sort(key=lambda m: m.start())
    seen: set[int] = set()
    deduped = []
    for m in matches:
        if m.start() not in seen:
            seen.add(m.start())
            deduped.append(m)
    return deduped


def split_sections(text: str) -> dict[str, str]:
    """
    Split paper body into canonically-named sections.

    1. Detect all ## headings with regex (zero LLM cost)
    2. Filter junk/table-header headings
    3. Map each name to a canonical name by scanning all words
    4. Merge sub-sections that share a canonical name
    5. Positional fallback if < 2 useful headings found
    """
    matches = _find_all_headings(text)

    raw_sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        try:
            raw = match.group(1)
        except IndexError:
            raw = match.group(0)
        name = _clean_name(raw)
        if _is_junk(name):
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            raw_sections.append((name, content))

    if len(raw_sections) < 2:
        return _positional_split(text)

    # Map to canonical names and merge sections with the same canonical name
    sections: dict[str, str] = {}
    for raw_name, content in raw_sections:
        canonical = _to_canonical(raw_name)
        if canonical in sections:
            sections[canonical] += "\n\n" + content
        else:
            sections[canonical] = content

    return sections


def _positional_split(text: str) -> dict[str, str]:
    n = len(text)
    if n == 0:
        return {"Body": ""}
    return {
        "Introduction": text[:int(n * 0.15)].strip(),
        "Methodology":  text[int(n * 0.15):int(n * 0.50)].strip(),
        "Results":      text[int(n * 0.50):int(n * 0.80)].strip(),
        "Conclusion":   text[int(n * 0.80):].strip(),
    }
