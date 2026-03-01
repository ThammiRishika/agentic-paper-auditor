import re
import xml.etree.ElementTree as ET
import requests
from crawl4ai import AsyncWebCrawler

ARXIV_API = "https://export.arxiv.org/api/query"
AR5IV_BASE = "https://ar5iv.org/abs"

# Matches: 1706.03762  /  2301.00001v2  /  abs/2301.00001
_ID_RE = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")


def extract_arxiv_id(url: str) -> str:
    match = _ID_RE.search(url)
    if not match:
        raise ValueError(f"Cannot extract arXiv ID from URL: {url!r}")
    return match.group(1)


def fetch_metadata(arxiv_id: str) -> dict:
    """Fetch structured metadata from the arXiv Atom API."""
    resp = requests.get(
        ARXIV_API,
        params={"id_list": arxiv_id, "max_results": 1},
        timeout=20,
    )
    resp.raise_for_status()

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(resp.text)
    entry = root.find("atom:entry", ns)

    if entry is None:
        raise ValueError(f"No arXiv entry found for id: {arxiv_id}")

    title = (entry.findtext("atom:title", namespaces=ns) or "").strip().replace("\n", " ")
    abstract = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
    published = (entry.findtext("atom:published", namespaces=ns) or "")[:10]

    authors = ", ".join(
        (a.findtext("atom:name", namespaces=ns) or "").strip()
        for a in entry.findall("atom:author", ns)
    )

    categories = [
        tag.get("term", "")
        for tag in entry.findall("arxiv:primary_category", ns)
    ]

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "categories": categories,
    }


async def fetch_body(arxiv_id: str) -> str:
    """
    Scrape full paper body from ar5iv.org using Crawl4AI.
    ar5iv renders arXiv LaTeX as clean, section-structured HTML → markdown.
    """
    url = f"{AR5IV_BASE}/{arxiv_id}"
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)

    body = result.markdown or ""
    # Token guard: ~60k chars ≈ 15k tokens (well within pipeline budget)
    return body[:60_000]


async def scrape(url: str) -> dict:
    """
    Hybrid scrape: arXiv API for metadata + Crawl4AI on ar5iv.org for body.
    Returns a merged paper dict ready for the decomposer.
    """
    arxiv_id = extract_arxiv_id(url)
    meta = fetch_metadata(arxiv_id)
    body = await fetch_body(arxiv_id)

    return {
        **meta,
        "arxiv_id": arxiv_id,
        "body": body,
    }
