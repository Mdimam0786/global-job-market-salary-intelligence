"""
Company Search -- browse and drill into companies from the Levels.fyi
dataset. Distinct from Job Postings Search (Page 4), which searches
individual postings: this page aggregates BY company first, then lets
you drill into one company's individual records.

(Mapped from the original spec's "Investor search" -- this project has
no investor/funding data; company benchmarking is the closest genuine
analog. See config/settings.py's NAV_SECTIONS and the app README.)

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_levels
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

MIN_SAMPLE_SIZE = 100  # consistent with the main project's Phase 5/10 company-ranking threshold


@st.cache_data(ttl=1800)
def _company_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("company").agg(
        n_reports=("record_id", "count"),
        median_comp=("total_yearly_compensation", "median"),
        avg_comp=("total_yearly_compensation", "mean"),
        top_title=("title", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
    ).reset_index()
    return summary


@st.cache_data(ttl=1800)
def _search_companies(summary: pd.DataFrame, query: str, min_reports: int) -> pd.DataFrame:
    result = summary.copy()
    if query:
        result = result[result["company"].str.contains(query, case=False, na=False)]
    result = result[result["n_reports"] >= min_reports]
    return result.sort_values("median_comp", ascending=False)


@handle_errors("Company Search")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🏢 Company Search")
    st.caption("Browse and benchmark companies from the Levels.fyi compensation dataset (62,642 self-reports).")

    levels = load_levels()
    if levels.empty:
        st.warning("No Levels.fyi data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    summary = _company_summary(levels)

    # ---- Search ----
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("🔍 Search company name", placeholder="e.g. 'Google', 'Amazon', 'Netflix'...")
    with col2:
        min_reports = st.number_input(
            "Min. reports", min_value=0, max_value=1000, value=MIN_SAMPLE_SIZE, step=10,
            help="Companies with fewer self-reports than this are hidden from ranked results by default, "
                 "consistent with the main project's Phase 5/10 credibility threshold. Set to 0 to see everyone.",
        )

    results = _search_companies(summary, query, min_reports)

    if min_reports < MIN_SAMPLE_SIZE:
        st.info(
            f"⚠️ Showing companies with fewer than {MIN_SAMPLE_SIZE} reports — treat rankings here as "
            "directional only, not reliable benchmarks (see Phase 5 EDA caveats)."
        )

    st.write("")
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Companies Found", f"{len(results):,}", gradient=1)
    with k2:
        kpi_card("Median Comp (top match)", f"${results['median_comp'].iloc[0]:,.0f}" if len(results) else "—", gradient=2)
    with k3:
        kpi_card("Total Reports Covered", f"{results['n_reports'].sum():,}" if len(results) else "0", gradient=3)

    if results.empty:
        st.info("No companies match this search.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.write("")
    st.markdown(f"#### Company rankings ({len(results):,})")
    st.dataframe(
        results.rename(columns={
            "company": "Company", "n_reports": "Reports", "median_comp": "Median Comp",
            "avg_comp": "Avg Comp", "top_title": "Most Common Title",
        }).style.format({"Median Comp": "${:,.0f}", "Avg Comp": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    csv_bytes = results.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download company rankings as CSV", data=csv_bytes, file_name="company_rankings.csv", mime="text/csv")

    st.write("")
    st.divider()

    # ---- Drill into one company ----
    st.markdown("#### Drill into a company")
    company_choice = st.selectbox("Select a company", options=results["company"].tolist())

    company_rows = levels[levels["company"] == company_choice]
    n = len(company_rows)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        kpi_card("Reports", f"{n:,}", gradient=1)
    with d2:
        kpi_card("Median Total Comp", f"${company_rows['total_yearly_compensation'].median():,.0f}", gradient=2)
    with d3:
        kpi_card("Median Base Salary", f"${company_rows['base_salary'].median():,.0f}", gradient=3)
    with d4:
        kpi_card("Median Years Exp.", f"{company_rows['years_of_experience'].median():.1f}", gradient=1)

    if n < MIN_SAMPLE_SIZE:
        st.warning(f"⚠️ Only {n} reports for {company_choice} — treat these figures as directional only (n<{MIN_SAMPLE_SIZE}).")

    try:
        import plotly.express as px
        title_summary = (
            company_rows.groupby("title")["total_yearly_compensation"]
            .agg(["median", "count"]).reset_index()
        )
        title_summary = title_summary[title_summary["count"] >= 5]  # avoid single-report title noise
        if not title_summary.empty:
            fig = px.bar(
                title_summary.sort_values("median"), x="median", y="title", orientation="h",
                labels={"median": "Median Total Comp (USD)", "title": ""},
                color_discrete_sequence=["#2A78D6"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=320,
            )
            with styled_container():
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough per-title volume at this company to break down by role.")
    except ImportError:
        st.info("Install `plotly` to see the title breakdown chart.")

    with st.expander(f"View all {n} individual reports for {company_choice}"):
        detail_cols = ["title", "city", "country", "total_yearly_compensation", "base_salary",
                       "stock_grant_value", "bonus", "years_of_experience"]
        st.dataframe(
            company_rows[detail_cols].rename(columns={
                "title": "Title", "city": "City", "country": "Country",
                "total_yearly_compensation": "Total Comp", "base_salary": "Base",
                "stock_grant_value": "Stock", "bonus": "Bonus", "years_of_experience": "Years Exp.",
            }).style.format({
                "Total Comp": "${:,.0f}", "Base": "${:,.0f}", "Stock": "${:,.0f}", "Bonus": "${:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
