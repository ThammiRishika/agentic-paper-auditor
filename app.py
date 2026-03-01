import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from pipeline.orchestrator import run_pipeline
from report.generator import generate_report, save_report
from scraper.arxiv_scraper import extract_arxiv_id

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Paper Auditor",
    page_icon="🔬",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-title { font-size: 2.4rem; font-weight: 800; margin-bottom: 0.2rem; }
    .subtitle   { color: #888; font-size: 1rem; margin-bottom: 1.5rem; }
    .score-card { background: #1e1e2e; border-radius: 10px; padding: 1rem; margin: 0.4rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🔬 Agentic Paper Auditor</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Multi-agent peer-review simulation</p>',
    unsafe_allow_html=True,
)

# ── Input ─────────────────────────────────────────────────────────────────────
url = st.text_input(
    "arXiv URL",
    placeholder="https://arxiv.org/abs/1706.03762",
    help="Paste any standard arXiv abstract URL",
)

analyze_btn = st.button("🚀 Analyze Paper", type="primary", disabled=not url)

# ── Agent step labels ─────────────────────────────────────────────────────────
STEP_LABELS = {
    "scraping":      "📥 Scraping arXiv paper…",
    "decomposing":   "✂️  Decomposing into sections…",
    "consistency":   "🔗 Consistency Agent running…",
    "grammar":       "✏️  Grammar & Language Agent running…",
    "novelty":       "🔍 Novelty Agent searching literature…",
    "fact_check":    "✅ Fact-Check Agent verifying claims…",
    "authenticity":  "🕵️ Authenticity Agent assessing fabrication risk…",
    "synthesizer":   "⚖️  Review Synthesizer generating verdict…",
}

if analyze_btn and url:
    # Quick relevance check: only arXiv-style URLs/IDs are supported.
    try:
        extract_arxiv_id(url)
    except Exception:
        st.warning(
            "This URL does not look like a valid arXiv paper link. "
            "Please provide a standard arXiv URL (e.g. `https://arxiv.org/abs/1706.03762`).\n\n"
            "We cannot audit non‑arXiv or irrelevant content."
        )
        st.stop()

    progress_placeholder = st.empty()
    steps_done: list[str] = []

    def progress_cb(step: str, msg: str = ""):
        label = STEP_LABELS.get(step, f"Running {step}…")
        steps_done.append(f"✅ {label.split('…')[0].strip()}")
        with progress_placeholder.container():
            st.status(f"**{label}**", state="running", expanded=True)
            for done in steps_done[:-1]:
                st.write(done)

    try:
        with st.spinner("Initialising pipeline…"):
            data = run_pipeline(url, progress_cb=progress_cb)

        progress_placeholder.empty()
        st.success("✅ Analysis complete!")

        report_md = generate_report(data)
        save_path  = save_report(report_md, data["paper"]["arxiv_id"])

        # ── Tabs: Report | Raw JSON ───────────────────────────────────────────
        tab_report, tab_json = st.tabs(["📄 Judgement Report", "🗂 Raw Outputs"])

        with tab_report:
            st.markdown(report_md)

        with tab_json:
            results = data["results"]
            for name, model in results.items():
                with st.expander(f"**{name.replace('_', ' ').title()}**"):
                    st.json(model.model_dump())

        # ── Download ──────────────────────────────────────────────────────────
        st.download_button(
            label="⬇️ Download Report (.md)",
            data=report_md,
            file_name=f"judgement_report_{data['paper']['arxiv_id']}.md",
            mime="text/markdown",
        )

    except Exception as e:
        progress_placeholder.empty()
        st.error(f"**Pipeline error:** {e}")
        st.exception(e)
