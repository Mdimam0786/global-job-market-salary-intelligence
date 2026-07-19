"""
SQL Insights -- showcases the main project's Phase 9 SQL analytics
layer. Displays the actual production SQL files with syntax
highlighting, plus a pandas-computed "live preview" of what each query
would return.

Honest note, consistent with the main project's
reports/sql_validation_notes.md: this app has no live PostgreSQL
connection either (same no-network constraint throughout this build).
"Live preview" means pandas logic that reproduces the SQL query's
result -- verified to match, but not literally executed against a SQL
engine within this app. This mirrors exactly how the main project
itself validated these queries (via SQLite + pandas cross-checks),
not a new or different shortcut invented for this page.

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container
from config.settings import REPO_ROOT

# After the project merge, these SQL files live under sql/<subfolder>/
# rather than one flat data/sql/ folder. Searched in this order.
SQL_SEARCH_DIRS = [
    REPO_ROOT / "sql" / "analysis_queries",
    REPO_ROOT / "sql" / "views",
    REPO_ROOT / "sql" / "procedures",
    REPO_ROOT / "sql" / "schema",
]


@st.cache_data(ttl=3600)
def _load_sql_file(filename: str) -> str:
    for directory in SQL_SEARCH_DIRS:
        path = directory / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
    searched = ", ".join(str(d / filename) for d in SQL_SEARCH_DIRS)
    return f"-- SQL file not found. Looked in: {searched}"


@st.cache_data(ttl=1800)
def _country_benchmark_preview(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas equivalent of vw_country_benchmarks / KPI 5 from
    01_business_kpis.sql."""
    summary = df.groupby("company_location").agg(
        n=("job_id", "count"),
        avg_salary=("salary_in_usd", "mean"),
        median_salary=("salary_in_usd", "median"),
    ).reset_index()
    summary = summary[summary["n"] >= 30]
    summary["salary_rank"] = summary["median_salary"].rank(ascending=False, method="min").astype(int)
    top = summary["median_salary"].max()
    summary["pct_of_top_country"] = (summary["median_salary"] / top * 100).round(1)
    return summary.sort_values("salary_rank")


@st.cache_data(ttl=1800)
def _remote_trend_preview(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas equivalent of vw_remote_work_trend / KPI 4."""
    yearly = df.groupby(["work_year", "work_setting"]).agg(
        n=("job_id", "count"), avg_salary=("salary_in_usd", "mean")
    ).reset_index()
    yearly["pct_of_postings"] = yearly.groupby("work_year")["n"].transform(lambda x: (x / x.sum() * 100).round(1))
    return yearly.sort_values(["work_year", "pct_of_postings"], ascending=[True, False])


@st.cache_data(ttl=1800)
def _top_titles_preview(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas equivalent of KPI 3 -- top 3 titles per category."""
    stats = df.groupby(["job_category", "job_title"]).agg(
        n=("job_id", "count"), avg_salary=("salary_in_usd", "mean")
    ).reset_index()
    stats = stats[stats["n"] >= 10]
    stats["rnk"] = stats.groupby("job_category")["avg_salary"].rank(ascending=False, method="dense")
    return stats[stats["rnk"] <= 3].sort_values(["job_category", "rnk"])


def _salary_benchmark_function(df: pd.DataFrame, job_category: str, experience_level: str, candidate_salary: float) -> dict:
    """Pandas re-implementation of get_salary_benchmark() from
    01_materialized_view_and_procedure.sql -- same logic validated in
    the main project's Phase 9/10."""
    comparable = df[(df["job_category"] == job_category) & (df["experience_level"] == experience_level)]
    n = len(comparable)
    if n == 0:
        return {"n": 0, "verdict": "No comparable data found."}

    median = comparable["salary_in_usd"].median()
    avg = comparable["salary_in_usd"].mean()
    p25 = comparable["salary_in_usd"].quantile(0.25)
    p75 = comparable["salary_in_usd"].quantile(0.75)
    percentile = (comparable["salary_in_usd"] <= candidate_salary).mean() * 100

    if n < 30:
        verdict = "Insufficient data for a reliable benchmark (n<30)"
    elif candidate_salary < p25:
        verdict = "Below market — consider negotiating"
    elif candidate_salary > p75:
        verdict = "Above market — strong offer"
    else:
        verdict = "Within typical market range"

    return {"n": n, "median": median, "avg": avg, "p25": p25, "p75": p75, "percentile": percentile, "verdict": verdict}


@handle_errors("SQL Insights")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🗄️ SQL Insights")
    st.caption(
        "The main project's production SQL layer (Phase 9) — CTEs, window functions, views, "
        "a materialized view, and a parameterized stored function."
    )

    with st.expander("ℹ️ How 'live preview' works on this page"):
        st.markdown(
            "This app has no live PostgreSQL connection (no network access in the build "
            "environment). Each 'Live Preview' below is a pandas re-implementation of the "
            "SQL query, verified to produce matching results — the same validation approach "
            "the main project itself used (see `reports/sql_validation_notes.md`), not a new "
            "shortcut invented for this page."
        )

    jobs = load_jobs()

    tab1, tab2, tab3, tab4 = st.tabs(["Business KPIs", "Views", "Materialized View + Procedure", "Try the Salary Benchmark Function"])

    with tab1:
        st.markdown("##### `sql/analysis_queries/01_business_kpis.sql`")
        st.code(_load_sql_file("01_business_kpis.sql"), language="sql", line_numbers=True)

        if not jobs.empty:
            st.write("")
            st.markdown("###### Live Preview: KPI 5 — Country Salary Benchmarking")
            st.dataframe(
                _country_benchmark_preview(jobs).rename(columns={
                    "company_location": "Country", "n": "n", "avg_salary": "Avg Salary",
                    "median_salary": "Median Salary", "salary_rank": "Rank", "pct_of_top_country": "% of Top Country",
                }).style.format({"Avg Salary": "${:,.0f}", "Median Salary": "${:,.0f}", "% of Top Country": "{:.1f}%"}),
                use_container_width=True, hide_index=True,
            )

            st.markdown("###### Live Preview: KPI 4 — Remote Work Trend")
            st.dataframe(
                _remote_trend_preview(jobs).rename(columns={
                    "work_year": "Year", "work_setting": "Setting", "n": "n",
                    "avg_salary": "Avg Salary", "pct_of_postings": "% of Postings",
                }).style.format({"Avg Salary": "${:,.0f}", "% of Postings": "{:.1f}%"}),
                use_container_width=True, hide_index=True, height=300,
            )

            st.markdown("###### Live Preview: KPI 3 — Top 3 Titles per Category (sample)")
            top_titles = _top_titles_preview(jobs)
            sample_cat = st.selectbox("Filter to category", options=sorted(top_titles["job_category"].unique()))
            st.dataframe(
                top_titles[top_titles["job_category"] == sample_cat].rename(columns={
                    "job_category": "Category", "job_title": "Title", "n": "n", "avg_salary": "Avg Salary", "rnk": "Rank",
                }).style.format({"Avg Salary": "${:,.0f}"}),
                use_container_width=True, hide_index=True,
            )

    with tab2:
        st.markdown("##### `sql/views/01_analytical_views.sql`")
        st.code(_load_sql_file("01_analytical_views.sql"), language="sql", line_numbers=True)
        st.caption(
            "These views wrap the KPI queries into reusable objects Power BI (or any BI tool) "
            "queries directly — see `reports/powerbi_dashboard_specification.md` for how each is used."
        )

    with tab3:
        st.markdown("##### `sql/procedures/01_materialized_view_and_procedure.sql`")
        st.code(_load_sql_file("01_materialized_view_and_procedure.sql"), language="sql", line_numbers=True)
        st.warning(
            "Unlike every other file on this page, this one was **syntax-reviewed only, not "
            "executed** anywhere — materialized views and PL/pgSQL stored functions have no "
            "SQLite equivalent, so even the main project's own validation pass couldn't run "
            "this directly (see `reports/sql_validation_notes.md`). The 'Try it' tab uses a "
            "pandas re-implementation of the underlying logic, which WAS validated."
        )

    with tab4:
        st.markdown("#### Try `get_salary_benchmark()` live")
        st.caption("Pandas re-implementation of the stored function's logic — same as validated in the main project's Phase 9/10.")

        if jobs.empty:
            st.warning("No data available.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                job_category = st.selectbox("Job Category", options=sorted(jobs["job_category"].unique()), key="sql_cat")
            with c2:
                experience_level = st.selectbox("Experience Level", options=["Entry-level", "Mid-level", "Senior", "Executive"], key="sql_exp")
            with c3:
                candidate_salary = st.number_input("Candidate/Offered Salary (USD)", min_value=15000, max_value=450000, value=150000, step=5000, key="sql_salary")

            if st.button("Run Benchmark", type="primary"):
                result = _salary_benchmark_function(jobs, job_category, experience_level, candidate_salary)

                if result["n"] == 0:
                    st.warning("No comparable data for this combination.")
                else:
                    k1, k2, k3 = st.columns(3)
                    with k1:
                        kpi_card("Comparable Records", f"{result['n']:,}", gradient=1)
                    with k2:
                        kpi_card("Market Median", f"${result['median']:,.0f}", gradient=2)
                    with k3:
                        kpi_card("Your Percentile", f"{result['percentile']:.0f}th", gradient=3)

                    verdict_color = "success" if "typical" in result["verdict"] else "warning" if "Insufficient" in result["verdict"] else "info"
                    getattr(st, verdict_color)(f"**Verdict:** {result['verdict']}")

    st.markdown("</div>", unsafe_allow_html=True)
