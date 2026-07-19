"""
EDA Explorer — interactive counterpart to the static reports/eda_insights.md
(101 insights from the main project's Phase 5). Lets a visitor filter the
primary fact table and see the charts/numbers recompute live, plus browse
and download the filtered raw rows via AgGrid.

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container, skeleton_loader
from config.theme import get_palette

EXPERIENCE_ORDER = ["Entry-level", "Mid-level", "Senior", "Executive"]


@st.cache_data(ttl=1800)
def _apply_filters(
    df: pd.DataFrame,
    experience_levels: list,
    categories: list,
    countries: list,
    remote_settings: list,
    year_range: tuple,
) -> pd.DataFrame:
    """Cached filter step, separate from the raw load, so re-filtering
    (common — every widget change reruns the script) doesn't re-read
    the CSV, only re-filters an already-in-memory DataFrame. Cache key
    includes every filter argument, so different filter combinations
    are cached independently rather than overwriting each other."""
    filtered = df.copy()
    if experience_levels:
        filtered = filtered[filtered["experience_level"].isin(experience_levels)]
    if categories:
        filtered = filtered[filtered["job_category"].isin(categories)]
    if countries:
        filtered = filtered[filtered["company_location"].isin(countries)]
    if remote_settings:
        filtered = filtered[filtered["work_setting"].isin(remote_settings)]
    filtered = filtered[
        (filtered["work_year"] >= year_range[0]) & (filtered["work_year"] <= year_range[1])
    ]
    return filtered


@handle_errors("EDA Explorer")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🔍 EDA Explorer")
    st.caption(
        "Interactive counterpart to the 101 findings in `reports/eda_insights.md` — "
        "filter the primary dataset and every chart below recomputes live."
    )

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available — nothing to explore yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---- Filters ----
    with st.expander("🎛️ Filters", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            experience_levels = st.multiselect(
                "Experience Level", options=EXPERIENCE_ORDER, default=[]
            )
        with f2:
            categories = st.multiselect(
                "Job Category", options=sorted(jobs["job_category"].unique()), default=[]
            )
        with f3:
            top_countries = jobs["company_location"].value_counts().head(20).index.tolist()
            countries = st.multiselect(
                "Company Location (top 20 shown)", options=sorted(top_countries), default=[]
            )
        with f4:
            remote_settings = st.multiselect(
                "Work Setting", options=sorted(jobs["work_setting"].unique()), default=[]
            )

        year_min, year_max = int(jobs["work_year"].min()), int(jobs["work_year"].max())
        year_range = st.slider("Work Year", min_value=year_min, max_value=year_max, value=(year_min, year_max))

    filtered = _apply_filters(
        jobs, experience_levels, categories, countries, remote_settings, year_range
    )

    if filtered.empty:
        st.warning("No rows match this filter combination — try widening it.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.caption(f"Showing **{len(filtered):,}** of {len(jobs):,} total postings ({len(filtered)/len(jobs)*100:.1f}%)")

    # ---- KPI row (recomputed on the filtered slice) ----
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Filtered Postings", f"{len(filtered):,}", gradient=1)
    with k2:
        kpi_card("Median Salary", f"${filtered['salary_in_usd'].median():,.0f}", gradient=2)
    with k3:
        kpi_card("Avg Salary", f"${filtered['salary_in_usd'].mean():,.0f}", gradient=3)
    with k4:
        remote_pct = (filtered["work_setting"] == "Remote").mean() * 100
        kpi_card("Remote Share", f"{remote_pct:.1f}%", gradient=1)

    if len(filtered) < 30:
        st.info(
            "⚠️ This filtered slice has fewer than 30 rows. Per the main project's "
            "Phase 5 EDA caveats, treat any percentage or ranking on a sample this "
            "small as directional only, not a reliable market signal."
        )

    st.write("")

    # ---- Charts ----
    try:
        import plotly.express as px

        palette = get_palette()
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### Median salary by job category")
            cat_summary = (
                filtered.groupby("job_category")["salary_in_usd"]
                .median()
                .sort_values(ascending=True)
                .reset_index()
            )
            fig1 = px.bar(
                cat_summary, x="salary_in_usd", y="job_category", orientation="h",
                labels={"salary_in_usd": "Median Salary (USD)", "job_category": ""},
                color_discrete_sequence=[palette["accent"]],
            )
            fig1.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=380,
            )
            with styled_container():
                st.plotly_chart(fig1, use_container_width=True)

        with chart_col2:
            st.markdown("#### Median salary trend by year")
            year_summary = filtered.groupby("work_year")["salary_in_usd"].median().reset_index()
            fig2 = px.line(
                year_summary, x="work_year", y="salary_in_usd", markers=True,
                labels={"work_year": "", "salary_in_usd": "Median Salary (USD)"},
                color_discrete_sequence=[palette["accent_2"]],
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=380,
            )
            with styled_container():
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Remote / Hybrid / In-person share by year")
        remote_summary = (
            filtered.groupby(["work_year", "work_setting"]).size().reset_index(name="count")
        )
        remote_summary["pct"] = remote_summary.groupby("work_year")["count"].transform(
            lambda x: x / x.sum() * 100
        )
        fig3 = px.line(
            remote_summary, x="work_year", y="pct", color="work_setting", markers=True,
            labels={"work_year": "", "pct": "% of postings", "work_setting": ""},
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10), height=320,
        )
        with styled_container():
            st.plotly_chart(fig3, use_container_width=True)

    except ImportError:
        st.info("Install `plotly` (see requirements.txt) to see interactive charts here.")
        skeleton_loader(3)

    st.write("")

    # ---- Data table: AgGrid with search / filter / pagination, + download ----
    st.markdown("#### Browse filtered rows")
    display_cols = [
        "job_id", "job_title", "job_category", "experience_level", "employment_type",
        "work_setting", "company_size", "company_location", "salary_in_usd", "work_year",
    ]
    table_df = filtered[[c for c in display_cols if c in filtered.columns]]

    try:
        from st_aggrid import AgGrid, GridOptionsBuilder

        gb = GridOptionsBuilder.from_dataframe(table_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        gb.configure_selection("single")
        grid_options = gb.build()

        AgGrid(
            table_df,
            gridOptions=grid_options,
            theme="alpine" if st.session_state.get("theme") != "dark" else "alpine-dark",
            fit_columns_on_grid_load=True,
            height=420,
        )
    except ImportError:
        st.warning(
            "`streamlit-aggrid` isn't installed — falling back to a standard table. "
            "Run `pip install streamlit-aggrid` for the full sortable/filterable grid "
            "(see requirements.txt)."
        )
        # Manual pagination fallback so the page still degrades gracefully rather
        # than dumping potentially thousands of rows into one static table.
        page_size = 25
        total_pages = max(1, -(-len(table_df) // page_size))  # ceiling division
        page_num = st.number_input(
            "Page", min_value=1, max_value=total_pages, value=1, step=1
        )
        start = (page_num - 1) * page_size
        st.dataframe(table_df.iloc[start : start + page_size], use_container_width=True)
        st.caption(f"Page {page_num} of {total_pages}")

    # ---- Download button ----
    csv_bytes = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_job_postings.csv",
        mime="text/csv",
    )

    st.markdown("</div>", unsafe_allow_html=True)
