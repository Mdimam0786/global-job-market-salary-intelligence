"""
Country Explorer -- map-first geographic exploration, distinct from the
prior search pages: this one leads with a choropleth map and supports
side-by-side comparison of multiple countries, rather than a text
search over individual records.

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

MIN_SAMPLE_SIZE = 30  # consistent with the main project's Phase 5/9 country-ranking threshold


@st.cache_data(ttl=1800)
def _country_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("company_location").agg(
        n_postings=("job_id", "count"),
        median_salary=("salary_in_usd", "median"),
        avg_salary=("salary_in_usd", "mean"),
        top_category=("job_category", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        remote_pct=("work_setting", lambda x: (x == "Remote").mean() * 100),
    ).reset_index()
    summary["rank"] = summary["median_salary"].rank(ascending=False, method="min").astype(int)
    return summary.sort_values("median_salary", ascending=False)


@handle_errors("Country Explorer")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🌍 Country Explorer")
    st.caption("Geographic breakdown of data-role salaries across 74 company locations.")

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    summary = _country_summary(jobs)
    reliable = summary[summary["n_postings"] >= MIN_SAMPLE_SIZE]

    # ---- Map ----
    st.markdown(f"#### Median salary by country (countries with >={MIN_SAMPLE_SIZE} postings shown at full confidence)")
    try:
        import plotly.express as px
        fig = px.choropleth(
            summary, locations="company_location", locationmode="country names",
            color="median_salary", hover_name="company_location",
            hover_data={"n_postings": True, "median_salary": ":.0f", "company_location": False},
            color_continuous_scale="Blues",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=420, geo=dict(bgcolor="rgba(0,0,0,0)"))
        with styled_container():
            st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"{len(summary) - len(reliable)} of {len(summary)} countries have fewer than "
            f"{MIN_SAMPLE_SIZE} postings -- their color on this map is based on a thin sample "
            "and shouldn't be read with high confidence (see Phase 5 EDA caveats)."
        )
    except ImportError:
        st.info("Install `plotly` to see the map.")

    st.write("")
    st.divider()

    # ---- Country deep dive ----
    st.markdown("#### Deep dive into a country")
    country_options = reliable["company_location"].tolist()
    selected_country = st.selectbox(
        f"Select a country (>={MIN_SAMPLE_SIZE} postings)", options=country_options
    )

    row = summary[summary["company_location"] == selected_country].iloc[0]
    country_jobs = jobs[jobs["company_location"] == selected_country]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Median Salary", f"${row['median_salary']:,.0f}", gradient=1)
    with k2:
        kpi_card("Global Rank", f"#{int(row['rank'])} of {len(summary)}", gradient=2)
    with k3:
        kpi_card("Postings", f"{int(row['n_postings']):,}", gradient=3)
    with k4:
        kpi_card("Remote Share", f"{row['remote_pct']:.1f}%", gradient=1)

    st.write("")
    chart_col1, chart_col2 = st.columns(2)
    try:
        import plotly.express as px

        with chart_col1:
            st.markdown("##### Salary trend by year")
            year_trend = country_jobs.groupby("work_year")["salary_in_usd"].median().reset_index()
            if len(year_trend) >= 2:
                fig1 = px.line(year_trend, x="work_year", y="salary_in_usd", markers=True,
                                labels={"work_year": "", "salary_in_usd": "Median Salary (USD)"},
                                color_discrete_sequence=["#2A78D6"])
                fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(l=10, r=10, t=10, b=10), height=300)
                with styled_container():
                    st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Not enough years of data to show a trend for this country.")

        with chart_col2:
            st.markdown("##### Top job categories")
            cat_counts = country_jobs["job_category"].value_counts().head(6).reset_index()
            cat_counts.columns = ["job_category", "count"]
            fig2 = px.bar(cat_counts, x="count", y="job_category", orientation="h",
                          labels={"count": "Postings", "job_category": ""},
                          color_discrete_sequence=["#1BAF7A"])
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=10, r=10, t=10, b=10), height=300,
                                yaxis={"categoryorder": "total ascending"})
            with styled_container():
                st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.info("Install `plotly` to see these charts.")

    st.write("")
    st.divider()

    # ---- Country comparison ----
    st.markdown("#### Compare countries side by side")
    compare_countries = st.multiselect(
        f"Select 2+ countries to compare (>={MIN_SAMPLE_SIZE} postings)",
        options=country_options, default=country_options[:3] if len(country_options) >= 3 else country_options,
    )

    if len(compare_countries) >= 2:
        compare_df = reliable[reliable["company_location"].isin(compare_countries)].sort_values(
            "median_salary", ascending=True
        )
        try:
            import plotly.express as px
            fig3 = px.bar(
                compare_df, x="median_salary", y="company_location", orientation="h",
                labels={"median_salary": "Median Salary (USD)", "company_location": ""},
                color_discrete_sequence=["#4A3AA7"],
            )
            fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=10, r=10, t=10, b=10), height=280)
            with styled_container():
                st.plotly_chart(fig3, use_container_width=True)
        except ImportError:
            pass

        st.dataframe(
            compare_df[["company_location", "n_postings", "median_salary", "remote_pct", "top_category"]]
            .rename(columns={
                "company_location": "Country", "n_postings": "Postings", "median_salary": "Median Salary",
                "remote_pct": "Remote %", "top_category": "Top Category",
            }).style.format({"Median Salary": "${:,.0f}", "Remote %": "{:.1f}%"}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Select at least 2 countries to compare.")

    # ---- Download ----
    st.write("")
    csv_bytes = summary.to_csv(index=False).encode("utf-8")
    st.download_button("Download full country summary as CSV", data=csv_bytes, file_name="country_summary.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)
