"""
Skill / Category Explorer -- two-tab page: browse job categories
(industry-like groupings in this dataset) and browse/search individual
skills with demand %, category, and related-skill recommendations
pulled from the Phase 6 association-rule table.

(Mapped from the original spec's "Industry search" -- this project has
no industry/vertical field; job_category and skill taxonomy are the
closest genuine analogs. See config/settings.py's NAV_SECTIONS.)

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_jobs, load_dim_skill, load_skill_bridge, load_skill_rules
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

MIN_CO_OCCURRENCE = 300  # consistent with the main project's Phase 8 recommender threshold


@st.cache_data(ttl=1800)
def _category_summary(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("job_category").agg(
        n_postings=("job_id", "count"),
        median_salary=("salary_in_usd", "median"),
        top_title=("job_title", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        remote_pct=("work_setting", lambda x: (x == "Remote").mean() * 100),
    ).reset_index().sort_values("median_salary", ascending=False)


@st.cache_data(ttl=1800)
def _skill_demand(dim_skill: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    total_respondents = bridge["response_id"].nunique()
    counts = bridge.groupby("skill_key")["response_id"].nunique().reset_index(name="n_respondents")
    merged = counts.merge(dim_skill, on="skill_key")
    merged["pct_of_respondents"] = merged["n_respondents"] / total_respondents * 100
    return merged.sort_values("n_respondents", ascending=False)


def _related_skills(rules: pd.DataFrame, skill_name: str, top_n: int = 5) -> pd.DataFrame:
    reliable = rules[rules["co_occurrence_count"] >= MIN_CO_OCCURRENCE]
    matches = reliable[(reliable["skill_a"] == skill_name) | (reliable["skill_b"] == skill_name)].copy()
    matches["related_skill"] = matches.apply(
        lambda r: r["skill_b"] if r["skill_a"] == skill_name else r["skill_a"], axis=1
    )
    return matches[["related_skill", "lift", "co_occurrence_count"]].sort_values("lift", ascending=False).head(top_n)


@handle_errors("Skill / Category Explorer")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🧩 Skill / Category Explorer")
    st.caption("Browse job categories, or search individual skills and see what pairs with them.")

    tab1, tab2 = st.tabs(["📂 Job Categories", "🛠️ Skills"])

    # ============ TAB 1: Job Categories ============
    with tab1:
        jobs = load_jobs()
        if jobs.empty:
            st.warning("No job postings data available.")
        else:
            cat_summary = _category_summary(jobs)
            st.markdown("#### All categories, ranked by median salary")

            try:
                import plotly.express as px
                fig = px.bar(
                    cat_summary.sort_values("median_salary"), x="median_salary", y="job_category",
                    orientation="h", labels={"median_salary": "Median Salary (USD)", "job_category": ""},
                    color_discrete_sequence=["#2A78D6"],
                )
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(l=10, r=10, t=10, b=10), height=400)
                with styled_container():
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.info("Install `plotly` to see this chart.")

            st.dataframe(
                cat_summary.rename(columns={
                    "job_category": "Category", "n_postings": "Postings", "median_salary": "Median Salary",
                    "top_title": "Most Common Title", "remote_pct": "Remote %",
                }).style.format({"Median Salary": "${:,.0f}", "Remote %": "{:.1f}%"}),
                use_container_width=True, hide_index=True,
            )

            st.write("")
            selected_cat = st.selectbox("Drill into a category", options=cat_summary["job_category"].tolist())
            cat_jobs = jobs[jobs["job_category"] == selected_cat]

            k1, k2, k3 = st.columns(3)
            with k1:
                kpi_card("Postings", f"{len(cat_jobs):,}", gradient=1)
            with k2:
                kpi_card("Median Salary", f"${cat_jobs['salary_in_usd'].median():,.0f}", gradient=2)
            with k3:
                kpi_card("Top Title", cat_jobs["job_title"].mode().iloc[0] if not cat_jobs.empty else "-", gradient=3)

    # ============ TAB 2: Skills ============
    with tab2:
        dim_skill = load_dim_skill()
        bridge = load_skill_bridge()
        rules = load_skill_rules()

        if dim_skill.empty or bridge.empty:
            st.warning("Skill data not available.")
        else:
            demand = _skill_demand(dim_skill, bridge)

            search_col, cat_col = st.columns([2, 1])
            with search_col:
                query = st.text_input("🔍 Search a skill", placeholder="e.g. 'Python', 'React', 'Docker'...")
            with cat_col:
                cat_filter = st.selectbox("Category", options=["All"] + sorted(demand["skill_category"].unique().tolist()))

            filtered_skills = demand.copy()
            if query:
                filtered_skills = filtered_skills[filtered_skills["skill_name"].str.contains(query, case=False, na=False)]
            if cat_filter != "All":
                filtered_skills = filtered_skills[filtered_skills["skill_category"] == cat_filter]

            st.markdown(f"#### Top skills ({len(filtered_skills)} matching)")
            try:
                import plotly.express as px
                top20 = filtered_skills.head(20).sort_values("n_respondents")
                fig2 = px.bar(
                    top20, x="pct_of_respondents", y="skill_name", orientation="h", color="skill_category",
                    labels={"pct_of_respondents": "% of Respondents", "skill_name": ""},
                )
                fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(l=10, r=10, t=10, b=10), height=460)
                with styled_container():
                    st.plotly_chart(fig2, use_container_width=True)
            except ImportError:
                st.info("Install `plotly` to see this chart.")

            st.write("")
            st.divider()

            # ---- Individual skill deep dive + related skills ----
            st.markdown("#### Skill deep dive")
            if filtered_skills.empty:
                st.info("No skills match this search.")
            else:
                selected_skill = st.selectbox("Select a skill", options=filtered_skills["skill_name"].tolist())
                skill_row = demand[demand["skill_name"] == selected_skill].iloc[0]

                k1, k2, k3 = st.columns(3)
                with k1:
                    kpi_card("Respondents", f"{int(skill_row['n_respondents']):,}", gradient=1)
                with k2:
                    kpi_card("% of Respondents", f"{skill_row['pct_of_respondents']:.1f}%", gradient=2)
                with k3:
                    kpi_card("Category", skill_row["skill_category"], gradient=3)

                if not rules.empty:
                    st.markdown(f"##### Skills that pair well with {selected_skill}")
                    related = _related_skills(rules, selected_skill)
                    if related.empty:
                        st.info(f"No reliable co-occurrence data for {selected_skill} (below the "
                                f"{MIN_CO_OCCURRENCE}-respondent confidence threshold).")
                    else:
                        st.dataframe(
                            related.rename(columns={
                                "related_skill": "Related Skill", "lift": "Lift", "co_occurrence_count": "Co-occurrences",
                            }),
                            use_container_width=True, hide_index=True,
                        )
                        st.caption(
                            "Lift > 1 means this pair co-occurs more often than random chance would predict "
                            "(see Phase 6/8 methodology). This is the same logic behind the main project's "
                            "skill-recommendation engine."
                        )

            csv_bytes = demand.to_csv(index=False).encode("utf-8")
            st.download_button("Download full skill demand table as CSV", data=csv_bytes,
                                file_name="skill_demand.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)
