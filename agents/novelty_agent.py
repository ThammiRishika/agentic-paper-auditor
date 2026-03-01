from agents.base_agent import extract_structured
from models.novelty import NoveltyResult
from tools.semantic_scholar import search_papers, format_search_results


def run_novelty(sections: dict, paper: dict) -> NoveltyResult:
    """
    Single-pass strategy:
      - Abstract + Introduction are short and always fit in one call.
      - Semantic Scholar results are fetched first and injected into the prompt.
    """
    abstract = sections.get("Abstract", paper.get("abstract", ""))
    introduction = sections.get("Introduction", "")
    related_work = sections.get("Related Work", sections.get("Background", ""))

    # Fetch related papers using title + first 200 chars of abstract as query
    query = f"{paper.get('title', '')} {abstract[:200]}"
    search_results = search_papers(query, limit=5)
    formatted = format_search_results(search_results)

    text = (abstract + "\n\n" + introduction + "\n\n" + related_work)[:8_000]

    title = paper.get("title", "")
    year = (paper.get("published") or "")[:4]

    prompt = f"""You are an expert academic reviewer assessing the novelty of a research paper.

PAPER METADATA:
- Title: {title}
- Year: {year or "Unknown"}

Important:
- If a search result has the SAME title as the paper under review, or is clearly a reimplementation
  or overview of this paper, treat it as evidence that this paper is foundational or widely cited,
  NOT as prior work that reduces its novelty.
- Be careful not to claim that the paper "builds upon" itself. Only describe it as building on
  genuinely earlier work.

Compare the paper's contributions against the related literature found via Semantic Scholar.
Assess whether the paper presents genuinely new ideas, methods, or results.

PAPER ABSTRACT + INTRODUCTION (+ optional related work):
{text}

RELATED PAPERS FROM SEMANTIC SCHOLAR:
{formatted}

Return a NoveltyResult with:
- novelty_index: qualitative assessment ("High", "Moderate", or "Low")
- related_papers: list of closely related papers found (title, authors, year, similarity)
- reasoning: explanation of the novelty assessment, citing specific overlaps if any
"""
    result = extract_structured(prompt, NoveltyResult)

    # Enrich related_papers with Semantic Scholar data if LLM returned empty list
    if not result.related_papers:
        from models.novelty import RelatedPaper

        for p in search_results:
            if "error" not in p:
                result.related_papers.append(
                    RelatedPaper(
                        title=p.get("title", ""),
                        authors=p.get("authors", ""),
                        year=p.get("year"),
                        similarity="Found via Semantic Scholar search",
                    )
                )

    return result
