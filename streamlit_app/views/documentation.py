"""
Documentation -- a browsable hub for every markdown doc the main
project produced, so a visitor doesn't need to dig through the repo.
Organized into categories matching how the docs were actually built
across the project's phases, not an arbitrary grouping.

Author: Md Imamuddin
"""

import streamlit as st

from utils.error_handler import handle_errors
from config.settings import REPO_ROOT

# After the project merge, docs live in three places at the repo root
# rather than one flat data/docs/ folder: the top-level README, docs/
# (design/reference docs), and reports/ (per-phase analysis writeups).
# Checked in this order for each filename.
DOC_SEARCH_DIRS = [REPO_ROOT, REPO_ROOT / "docs", REPO_ROOT / "reports"]

CATEGORIES = {
    "📘 Project Docs": {
        "README": "README.md",
        "Data Dictionary": "data_dictionary.md",
        "Business Glossary": "business_glossary.md",
        "Technical Design Document": "technical_design_document.md",
    },
    "📊 Analysis Reports": {
        "Data Quality Report (Phase 3)": "data_quality_report.md",
        "EDA Insights — 101 Findings (Phase 5)": "eda_insights.md",
        "NLP & Skill Analysis (Phase 6)": "nlp_skill_analysis.md",
        "Statistical Analysis (Phase 7)": "statistical_analysis.md",
        "ML Analysis (Phase 8)": "ml_analysis.md",
        "SQL Validation Notes (Phase 9)": "sql_validation_notes.md",
        "Power BI Dashboard Specification (Phase 10)": "powerbi_dashboard_specification.md",
    },
    "🎯 Career": {
        "Resume Bullets & Interview Prep": "resume_and_interview_prep.md",
    },
    "🚀 Publishing": {
        "GitHub Publishing Checklist": "github_publishing_checklist.md",
    },
}


@st.cache_data(ttl=3600)
def _load_doc(filename: str) -> str:
    for directory in DOC_SEARCH_DIRS:
        path = directory / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
    searched = ", ".join(str(d / filename) for d in DOC_SEARCH_DIRS)
    return f"*Document not found. Looked in: {searched}*"


@handle_errors("Documentation")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("📚 Documentation")
    st.caption("Every document the main project produced, browsable in one place.")

    col_nav, col_content = st.columns([1, 3])

    with col_nav:
        st.markdown("##### Browse")
        selected_doc = None
        for category, docs in CATEGORIES.items():
            with st.expander(category, expanded=(category == "📘 Project Docs")):
                for label, filename in docs.items():
                    if st.button(label, key=f"doc_{filename}", use_container_width=True):
                        st.session_state["selected_doc"] = filename
                        st.session_state["selected_doc_label"] = label

        if "selected_doc" not in st.session_state:
            st.session_state["selected_doc"] = "README.md"
            st.session_state["selected_doc_label"] = "README"

    with col_content:
        content = _load_doc(st.session_state["selected_doc"])
        st.markdown(f"### {st.session_state['selected_doc_label']}")
        st.download_button(
            "⬇️ Download this document",
            data=content.encode("utf-8"),
            file_name=st.session_state["selected_doc"],
            mime="text/markdown",
        )
        st.divider()
        st.markdown(content)

    st.markdown("</div>", unsafe_allow_html=True)
