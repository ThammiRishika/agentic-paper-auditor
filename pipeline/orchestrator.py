import asyncio
import time
from typing import Callable, Optional

from dotenv import load_dotenv

load_dotenv()

from scraper.arxiv_scraper import scrape
from decomposer.section_splitter import split_sections
from agents.consistency_agent import run_consistency
from agents.grammar_agent import run_grammar
from agents.novelty_agent import run_novelty
from agents.factcheck_agent import run_factcheck
from agents.authenticity_agent import run_authenticity
from agents.synthesizer_agent import run_synthesizer


def run_pipeline(
    url: str,
    progress_cb: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """
    Full pipeline: scrape (async) → decompose → 6 agents (sync).

    The scraping step is the only async part (Crawl4AI requirement).
    All LLM agent calls are synchronous and run OUTSIDE the event loop
    to avoid httpx/asyncio conflicts when instructor calls the local server.
    """

    def notify(step: str, msg: str = ""):
        if progress_cb:
            progress_cb(step, msg)

    # 1. Scrape (async — run in its own event loop then exit) 
    notify("scraping", "Fetching paper from arXiv…")
    paper = asyncio.run(scrape(url))  # event loop opened and CLOSED here

    # 2. Decompose (pure Python, no LLM) 
    notify("decomposing", "Splitting paper into sections…")
    sections = split_sections(paper["body"])
    if "Abstract" not in sections and paper.get("abstract"):
        sections["Abstract"] = paper["abstract"]

    # 3. Agents (all synchronous, no active event loop) 
    notify("consistency", "Running Consistency Agent…")
    consistency = run_consistency(sections)
    time.sleep(12)

    notify("grammar", "Running Grammar & Language Agent…")
    grammar = run_grammar(sections)
    time.sleep(12)

    notify("novelty", "Running Novelty Agent (Semantic Scholar)…")
    novelty = run_novelty(sections, paper)
    time.sleep(12)

    notify("fact_check", "Running Fact-Check Agent…")
    factcheck = run_factcheck(sections)
    time.sleep(12)

    notify("authenticity", "Running Authenticity Agent…")
    authenticity = run_authenticity(sections, paper)
    time.sleep(12)

    notify("synthesizer", "Running Review Synthesizer…")
    verdict = run_synthesizer(consistency, grammar, novelty, factcheck, authenticity)

    return {
        "paper": paper,
        "sections": list(sections.keys()),
        "results": {
            "consistency": consistency,
            "grammar": grammar,
            "novelty": novelty,
            "fact_check": factcheck,
            "authenticity": authenticity,
            "verdict": verdict,
        },
    }
