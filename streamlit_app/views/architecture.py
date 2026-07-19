"""
Project Architecture -- shows both the underlying data platform's
architecture (Phases 1-11 of the main project) and this Streamlit
app's own architecture, plus a consolidated, honest list of every
environment constraint and substitution made across the whole build.

Uses st.graphviz_chart -- verified working in this environment (the
graphviz Python package + system `dot` binary were both confirmed
present and functional before relying on this, unlike most of this
app's other library dependencies which are NOT installed here).

Author: Md Imamuddin
"""

import streamlit as st

from utils.error_handler import handle_errors
from utils.ui_components import styled_container


@handle_errors("Project Architecture")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🏗️ Project Architecture")
    st.caption("How the data platform and this Streamlit companion app fit together.")

    tab1, tab2, tab3 = st.tabs(["Data Platform", "Streamlit App", "Environment Constraints"])

    # ============ TAB 1: Data Platform ============
    with tab1:
        st.markdown("#### End-to-end data platform (main project)")
        try:
            graph = """
            digraph {
                rankdir=TB;
                node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.2,0.12"];
                edge [color="#9CA3AF"];

                A1 [label="jobs_in_data_2024\\n14,199 rows", fillcolor="#DCEBFC", color="#2A78D6"];
                A2 [label="Stack Overflow Survey\\n65,437 respondents", fillcolor="#DCEBFC", color="#2A78D6"];
                A3 [label="Levels.fyi\\n62,642 reports", fillcolor="#DCEBFC", color="#2A78D6"];

                B [label="ETL & Cleaning\\nPython, pandas, outlier flags", fillcolor="#EAEAEA", color="#6B7280"];

                C [label="PostgreSQL Star Schema\\n3 fact tables, 9 dimensions", fillcolor="#EAEAEA", color="#6B7280"];

                D1 [label="SQL Analytics\\nKPIs, views, CTEs", fillcolor="#DCEBFC", color="#2A78D6"];
                D2 [label="ML Models\\nSalary, clustering, NLP", fillcolor="#DCEBFC", color="#2A78D6"];
                D3 [label="Power BI Dashboards\\n10 report pages", fillcolor="#DCEBFC", color="#2A78D6"];

                E [label="Documentation\\nREADME, glossary, specs", fillcolor="#EAEAEA", color="#6B7280"];

                A1 -> B; A2 -> B; A3 -> B;
                B -> C;
                C -> D1; C -> D2; C -> D3;
                D1 -> E; D2 -> E; D3 -> E;
            }
            """
            with styled_container():
                st.graphviz_chart(graph, use_container_width=True)
        except Exception:
            st.info("Graphviz rendering unavailable in this environment — see `reports/` for the written architecture documentation.")

        st.caption(
            "Three real datasets, never merged into one fact table (see the main project's "
            "Phase 3/4 rationale) — a galaxy schema with shared dimensions instead."
        )

    # ============ TAB 2: Streamlit App ============
    with tab2:
        st.markdown("#### This app's architecture")
        try:
            graph2 = """
            digraph {
                rankdir=TB;
                node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.2,0.12"];
                edge [color="#9CA3AF"];

                APP [label="app.py\\nsession-state router + sidebar", fillcolor="#F4E8D8", color="#EDA100"];
                CFG [label="config/\\nsettings.py, theme.py", fillcolor="#EAEAEA", color="#6B7280"];
                UTILS [label="utils/\\nlogger, data_loader, error_handler, ui_components", fillcolor="#EAEAEA", color="#6B7280"];
                VIEWS [label="views/\\none module per page", fillcolor="#DCEBFC", color="#2A78D6"];
                DATA [label="data/\\nprocessed CSVs + SQL files", fillcolor="#EAEAEA", color="#6B7280"];

                APP -> CFG; APP -> UTILS; APP -> VIEWS;
                VIEWS -> UTILS;
                UTILS -> DATA;
            }
            """
            with styled_container():
                st.graphviz_chart(graph2, use_container_width=True)
        except Exception:
            st.info("Graphviz rendering unavailable in this environment.")

        st.markdown(
            """
            - **Router, not native multipage** — `views/` (not `pages/`) deliberately, to avoid
              colliding with Streamlit's auto-detected native navigation, since this app needs a
              fully custom sidebar (sections, icons, dark/light toggle)
            - **Caching layers** — `st.cache_data` for DataFrames (data loaders, filtered views),
              `st.cache_resource` for the trained ML models (Pages 8-10 share one cached model,
              not three separate copies)
            - **Session state** — theme preference, current page, search pagination position,
              and the last salary prediction all persist across reruns
            """
        )

    # ============ TAB 3: Environment Constraints ============
    with tab3:
        st.markdown("#### Every substitution made in this build, in one place")
        st.caption(
            "Consolidated from every page's individual disclosures — the point of this tab is "
            "that none of these were hidden at the time they mattered, and here they all are "
            "again in one list for anyone auditing the project quickly."
        )

        constraints = [
            ("No network access", "Every `pip install` for XGBoost, LightGBM, SHAP, statsmodels, wordcloud, DuckDB, Streamlit, Plotly, and AgGrid failed. Code was written to the correct APIs and validated via plain pandas/sklearn where possible, but never executed as a running Streamlit app."),
            ("No PostgreSQL server", "The Phase 4 star schema DDL was written but validated via SQLite (which supports the same CTEs/window functions) plus manual pandas cross-checks for `PERCENTILE_CONT`, which SQLite lacks."),
            ("No Power BI Desktop", "DAX measures, Power Query M, and a theme JSON were written and are paste-ready, but the actual `.pbix` was never assembled or screenshot-tested."),
            ("SHAP unavailable", "Substituted with scikit-learn's `permutation_importance` for global feature importance — genuinely useful, but without SHAP's per-prediction Shapley-value guarantees or interaction terms."),
            ("XGBoost/LightGBM unavailable", "Substituted with scikit-learn's `GradientBoostingRegressor`/`RandomForestRegressor` — same algorithm family, smaller hyperparameter surface."),
            ("A real bug, found and fixed", "Re-implementing the Phase 8 classification pipeline for this app's Page 9 surfaced a genuine `ColumnTransformer` bug in the main project — `salary_in_usd` was silently dropped despite being documented as a feature. Fixed in both places, with before/after numbers kept visible rather than replaced."),
        ]

        for title, detail in constraints:
            with styled_container():
                st.markdown(f"**{title}**")
                st.caption(detail)

    st.markdown("</div>", unsafe_allow_html=True)
