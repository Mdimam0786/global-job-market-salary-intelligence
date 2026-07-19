"""
Home / Landing page.

Author: Md Imamuddin
"""

import streamlit as st

from utils.data_loader import compute_home_kpis, load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, status_indicator, styled_container
from config.settings import NAV_SECTIONS


@handle_errors("Home")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    # ---- Hero ----
    st.markdown("# Global Job Market & Salary Intelligence")
    st.markdown(
        "##### An end-to-end analytics platform on real, public job-market data — "
        "SQL, statistics, machine learning, and Power BI, built with full "
        "data-quality transparency at every step."
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        status_indicator("Data pipeline: validated (Phase 3)", "live")
    with col_b:
        status_indicator("Power BI: primary BI layer — this app is a companion showcase", "warn")

    st.write("")

    # ---- KPI row ----
    kpis = compute_home_kpis()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Postings", f'{kpis["total_postings"]:,}', gradient=1)
    with c2:
        kpi_card("Average Salary", f'${kpis["avg_salary"]:,}', gradient=2)
    with c3:
        kpi_card("Company Locations", f'{kpis["company_locations"]}', gradient=3)
    with c4:
        kpi_card("Remote Share (all years)", f'{kpis["remote_pct"]}%', gradient=1)

    st.write("")
    st.write("")

    # ---- Quick nav cards to major sections ----
    st.markdown("### Explore the platform")
    nav_cols = st.columns(3)
    quick_links = [
        ("🔍 EDA Explorer", "eda", "101 grounded insights across salary, skills, and geography."),
        ("💰 Salary Prediction", "funding_prediction", "ML models predicting salary from role and location."),
        ("🗄️ SQL Insights", "sql_insights", "Production SQL — CTEs, window functions, KPIs."),
    ]
    for col, (label, key, desc) in zip(nav_cols, quick_links):
        with col:
            with styled_container():
                st.markdown(f"**{label}**")
                st.caption(desc)
                if st.button("Open →", key=f"quicknav_{key}", use_container_width=True):
                    st.session_state.current_page = key
                    st.rerun()

    st.write("")

    # ---- Preview chart (a light, fast one for the landing page) ----
    st.markdown("### Median salary by experience level")
    jobs = load_jobs()
    if not jobs.empty and "experience_level" in jobs.columns and "salary_in_usd" in jobs.columns:
        try:
            import plotly.express as px

            order = ["Entry-level", "Mid-level", "Senior", "Executive"]
            summary = (
                jobs.groupby("experience_level", observed=True)["salary_in_usd"]
                .median()
                .reindex(order)
                .reset_index()
            )
            fig = px.bar(
                summary,
                x="experience_level",
                y="salary_in_usd",
                labels={"experience_level": "", "salary_in_usd": "Median Salary (USD)"},
                color_discrete_sequence=["#2A78D6"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
            )
            with styled_container():
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install `plotly` to see this chart (see requirements.txt).")
    else:
        st.info("Job postings data not found yet — add `jobs_fact_clean.csv` to `data/processed/`.")

    st.markdown("</div>", unsafe_allow_html=True)
