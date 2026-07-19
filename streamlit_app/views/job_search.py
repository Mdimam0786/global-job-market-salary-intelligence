"""
Job Postings Search -- search-first UX over the primary fact table.
Distinct in purpose from EDA Explorer (analytical, chart-first): this
page is a search engine over individual postings, with a text query,
facets, a results table, and a click-through detail view.

(Mapped from the original spec's "Startup search" -- see
config/settings.py's NAV_SECTIONS comment and the app README for the
full page-name mapping to this project's actual domain.)

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

PAGE_SIZE = 20


@st.cache_data(ttl=1800)
def _search(
    df: pd.DataFrame,
    query: str,
    experience_levels: list,
    categories: list,
    countries: list,
    salary_range: tuple,
    sort_by: str,
    ascending: bool,
) -> pd.DataFrame:
    result = df.copy()
    if query:
        result = result[result["job_title"].str.contains(query, case=False, na=False)]
    if experience_levels:
        result = result[result["experience_level"].isin(experience_levels)]
    if categories:
        result = result[result["job_category"].isin(categories)]
    if countries:
        result = result[result["company_location"].isin(countries)]
    result = result[
        (result["salary_in_usd"] >= salary_range[0]) & (result["salary_in_usd"] <= salary_range[1])
    ]
    return result.sort_values(sort_by, ascending=ascending)


@handle_errors("Job Postings Search")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🔎 Job Postings Search")
    st.caption("Search and filter individual postings from the primary dataset (14,199 records).")

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---- Search bar ----
    query = st.text_input("🔍 Search job titles", placeholder="e.g. 'Data Scientist', 'ML Engineer', 'Analyst'...")

    # ---- Facet filters ----
    with st.expander("🎛️ Refine results", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            experience_levels = st.multiselect(
                "Experience Level", options=["Entry-level", "Mid-level", "Senior", "Executive"]
            )
        with f2:
            categories = st.multiselect("Job Category", options=sorted(jobs["job_category"].unique()))
        with f3:
            top_countries = jobs["company_location"].value_counts().head(20).index.tolist()
            countries = st.multiselect("Company Location", options=sorted(top_countries))

        sal_min, sal_max = int(jobs["salary_in_usd"].min()), int(jobs["salary_in_usd"].max())
        salary_range = st.slider(
            "Salary Range (USD)", min_value=sal_min, max_value=sal_max, value=(sal_min, sal_max), step=5000
        )

        s1, s2 = st.columns(2)
        with s1:
            sort_by = st.selectbox(
                "Sort by", options=["salary_in_usd", "work_year", "job_title"],
                format_func=lambda x: {"salary_in_usd": "Salary", "work_year": "Year", "job_title": "Title"}[x],
            )
        with s2:
            ascending = st.selectbox("Order", options=[False, True], format_func=lambda x: "Descending" if not x else "Ascending")

    results = _search(jobs, query, experience_levels, categories, countries, salary_range, sort_by, ascending)

    # ---- Result count + quick stats ----
    st.write("")
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Results Found", f"{len(results):,}", gradient=1)
    with k2:
        kpi_card("Median Salary", f"${results['salary_in_usd'].median():,.0f}" if len(results) else "-", gradient=2)
    with k3:
        kpi_card("Unique Locations", f"{results['company_location'].nunique():,}" if len(results) else "0", gradient=3)

    if results.empty:
        st.info("No postings match this search -- try broadening your filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.write("")

    # ---- Small results map (contextual, not the full Geographic Analysis page) ----
    try:
        import plotly.express as px
        geo_summary = results.groupby("company_location").agg(
            count=("job_id", "count"), median_salary=("salary_in_usd", "median")
        ).reset_index()
        fig = px.choropleth(
            geo_summary, locations="company_location", locationmode="country names",
            color="count", hover_data=["median_salary"],
            color_continuous_scale="Blues",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=280, geo=dict(bgcolor="rgba(0,0,0,0)"))
        with styled_container():
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install `plotly` to see the results map.")

    st.write("")

    # ---- Paginated results table ----
    st.markdown(f"#### Results ({len(results):,})")
    total_pages = max(1, -(-len(results) // PAGE_SIZE))

    if "search_page" not in st.session_state:
        st.session_state.search_page = 1
    if st.session_state.search_page > total_pages:
        st.session_state.search_page = 1

    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    with page_col2:
        st.session_state.search_page = st.slider(
            "Page", min_value=1, max_value=total_pages, value=st.session_state.search_page,
            label_visibility="collapsed",
        )
    st.caption(f"Page {st.session_state.search_page} of {total_pages}")

    start = (st.session_state.search_page - 1) * PAGE_SIZE
    page_results = results.iloc[start : start + PAGE_SIZE]

    display_cols = ["job_title", "job_category", "experience_level", "company_location", "salary_in_usd", "work_year", "work_setting"]
    st.dataframe(
        page_results[display_cols].rename(columns={
            "job_title": "Title", "job_category": "Category", "experience_level": "Level",
            "company_location": "Location", "salary_in_usd": "Salary (USD)", "work_year": "Year",
            "work_setting": "Setting",
        }).style.format({"Salary (USD)": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

    # ---- Detail view: pick a row to inspect ----
    st.write("")
    st.markdown("#### Inspect a specific posting")
    row_options = {
        f"{row.job_title} -- {row.company_location} -- ${row.salary_in_usd:,.0f}": row.job_id
        for row in page_results.itertuples()
    }
    if row_options:
        selected_label = st.selectbox("Select a posting from this page", options=list(row_options.keys()))
        selected_id = row_options[selected_label]
        detail = jobs[jobs["job_id"] == selected_id].iloc[0]

        with styled_container():
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown(f"**Title:** {detail['job_title']}")
                st.markdown(f"**Category:** {detail['job_category']}")
                st.markdown(f"**Experience:** {detail['experience_level']}")
            with d2:
                st.markdown(f"**Salary:** ${detail['salary_in_usd']:,.0f}")
                st.markdown(f"**Employment:** {detail['employment_type']}")
                st.markdown(f"**Company Size:** {detail['company_size']}")
            with d3:
                st.markdown(f"**Company Location:** {detail['company_location']}")
                st.markdown(f"**Employee Residence:** {detail['employee_residence']}")
                st.markdown(f"**Work Setting:** {detail['work_setting']}")
            if bool(detail.get("salary_is_outlier", False)):
                st.warning("This salary was flagged as a statistical outlier (IQR method) in Phase 3 -- shown, not excluded.")

    # ---- Download ----
    st.write("")
    csv_bytes = results[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download all search results as CSV",
        data=csv_bytes,
        file_name="job_search_results.csv",
        mime="text/csv",
    )

    st.markdown("</div>", unsafe_allow_html=True)
