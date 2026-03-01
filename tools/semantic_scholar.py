import requests
from typing import Any

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

FIELDS = "title,authors,year,abstract,externalIds"


def search_papers(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search Semantic Scholar for papers related to the query.
    Free API, no key required.
    Returns a list of dicts with title, authors, year, abstract.
    """
    try:
        resp = requests.get(
            SEMANTIC_SCHOLAR_API,
            params={"query": query, "limit": limit, "fields": FIELDS},
            timeout=15,
            headers={"User-Agent": "agentic-paper-auditor/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        papers = []
        for p in data.get("data", []):
            papers.append(
                {
                    "title": p.get("title", ""),
                    "authors": ", ".join(a.get("name", "") for a in p.get("authors", [])),
                    "year": p.get("year"),
                    "abstract": (p.get("abstract") or "")[:400],  # brief excerpt
                }
            )
        return papers
    except Exception as e:
        return [{"error": str(e)}]


def format_search_results(papers: list[dict]) -> str:
    """Format search results as plain text for inclusion in an LLM prompt."""
    if not papers:
        return "No related papers found."
    lines = []
    for i, p in enumerate(papers, 1):
        if "error" in p:
            lines.append(f"{i}. [Search error: {p['error']}]")
            continue
        year = f" ({p['year']})" if p.get("year") else ""
        lines.append(f"{i}. {p['title']}{year} — {p['authors']}")
        if p.get("abstract"):
            lines.append(f"   Abstract: {p['abstract']}")
    return "\n".join(lines)
