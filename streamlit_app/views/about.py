"""
About / Contact -- the final page. GitHub link, LinkedIn link, resume
download, and a project summary.

Author: Md Imamuddin
"""

import streamlit as st

from utils.data_loader import compute_home_kpis
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container
from config.settings import GITHUB_URL, LINKEDIN_URL, RESUME_PATH, BASE_DIR


@handle_errors("About")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("👤 About This Project")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            #### Global Job Market & Salary Intelligence Platform

            An end-to-end analytics project built on three real, independently-collected
            public datasets — no synthetic data anywhere. Covers data engineering, SQL,
            statistics, machine learning, NLP, Power BI, and this Streamlit companion app.

            **What this project is built to demonstrate:**
            - Real execution wherever the environment allowed it, honest disclosure everywhere it didn't
            - Catching and fixing actual bugs (see Project Architecture → Environment Constraints,
              and the Model Explainability / Experience-Level Prediction pages) rather than only
              presenting a polished final state
            - Treating "three different populations, never blended" as a real design discipline,
              not just a one-time decision

            **Note:** Power BI remains the primary BI deliverable for this project — this app is
            a companion showcase, not a replacement. See the Project Architecture page for how
            they relate.
            """
        )

    with col2:
        with styled_container():
            st.markdown("##### Connect")

            st.markdown(f"🔗 [GitHub Repository]({GITHUB_URL})")
            st.markdown(f"💼 [LinkedIn Profile]({LINKEDIN_URL})")
            st.markdown("📧 **Email:** [mdimamuddinf786@gmail.com](mailto:mdimamuddinf786@gmail.com)")

            

            st.write("")
            if RESUME_PATH.exists():
                with open(RESUME_PATH, "rb") as f:
                    st.download_button(
                        "📄 Download Resume", data=f.read(),
                        file_name="resume.pdf", mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.info(
                    "📄 Resume not yet added — place a `resume.pdf` at "
                    f"`{RESUME_PATH.relative_to(BASE_DIR)}` to enable this download button."
                )

    st.write("")
    st.divider()

    st.markdown("#### Project by the numbers")
    kpis = compute_home_kpis()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Job Postings Analyzed", f'{kpis["total_postings"]:,}', gradient=1)
    with c2:
        kpi_card("Datasets Integrated", "3", gradient=2, delta="142,278 combined rows")
    with c3:
        kpi_card("Pages in This App", "14", gradient=3)
    with c4:
        kpi_card("ML Models Built", "5+", gradient=1)

    st.write("")
    st.markdown("#### Tech stack")
    stack_cols = st.columns(6)
    stack = ["Python", "pandas", "scikit-learn", "SQL", "Power BI", "Streamlit"]
    for col, tech in zip(stack_cols, stack):
        with col:
            st.markdown(f"<div style='text-align:center; padding: 8px;'>{tech}</div>", unsafe_allow_html=True)

    st.write("")
    st.caption(
        "Built as a portfolio project with an emphasis on honest engineering judgment: "
        "every substitution, limitation, and bug found along the way is documented rather "
        "than smoothed over. See the Documentation page for the full paper trail."
    )

    st.markdown("</div>", unsafe_allow_html=True)
