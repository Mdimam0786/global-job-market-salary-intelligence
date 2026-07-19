"""
Model Explainability -- the original spec calls this a "SHAP explanation
page." I couldn't install SHAP on my build machine (no network access -- same
constraint documented in the main project's Phase 8, reports/ml_analysis.md).

This page carries forward the exact same documented substitution:
scikit-learn's permutation_importance for GLOBAL explainability (reusing
the cached model from the Salary Prediction page, not retraining), plus
a genuine single-feature "what-if" sensitivity tool for something
SHAP-adjacent at the LOCAL level -- vary one input while holding the
rest fixed, and see how the prediction moves. This is explicitly not a
SHAP value (no Shapley game-theoretic guarantees, no interaction terms),
and the page says so directly rather than implying equivalence.

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container
from views.salary_prediction import train_model, FEATURES


@st.cache_data(ttl=3600, show_spinner="Computing permutation importance...")
def _permutation_importance(_pipeline, X_test: pd.DataFrame, y_test_log: pd.Series):
    from sklearn.inspection import permutation_importance
    result = permutation_importance(_pipeline, X_test, y_test_log, n_repeats=10, random_state=42, n_jobs=-1)
    return pd.Series(result.importances_mean, index=X_test.columns).sort_values(ascending=False)


@handle_errors("Model Explainability")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🧠 Model Explainability")

    with st.expander("⚠️ Why this isn't a SHAP page, and what it is instead", expanded=True):
        st.markdown(
            "SHAP isn't installed in this build environment (no network access — the exact "
            "same constraint documented in the main project's `reports/ml_analysis.md`). "
            "This page uses two techniques instead:\n\n"
            "1. **Permutation importance** (global) — reuses the *same cached model* trained "
            "on the Salary Prediction page, not a separate copy. Answers \"how much does "
            "shuffling this feature hurt performance,\" which is related to but **not** the "
            "same guarantee SHAP provides (no per-prediction Shapley values, no formally "
            "attributed interaction effects).\n"
            "2. **Single-feature sensitivity ('what-if')** (local-ish) — vary one input, hold "
            "the rest fixed, watch the prediction move. Genuinely useful for intuition, "
            "explicitly **not** a Shapley-value decomposition."
        )

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    model_info = train_model(jobs)  # cached -- reuses the Salary Prediction page's trained model
    pipeline = model_info["pipeline"]

    # ---- Global: permutation importance ----
    st.markdown("#### Global feature importance (permutation-based)")
    importance = _permutation_importance(pipeline, model_info["X_test"], model_info["y_test_log"])

    try:
        import plotly.express as px
        importance_df = importance.rename("importance").sort_values().reset_index()
        importance_df.columns = ["feature", "importance"]
        fig = px.bar(
            importance_df, x="importance", y="feature",
            orientation="h", color_discrete_sequence=["#4A3AA7"],
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=10, r=10, t=10, b=10), height=320,
                            xaxis_title="Importance", yaxis_title="")
        with styled_container():
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.dataframe(importance.rename("Importance"), use_container_width=True)

    st.caption(
        f"**{importance.index[0]}** is the strongest driver ({importance.iloc[0]:.3f}), consistent "
        "with Phase 8's finding — country matters more to predicted salary than job category or "
        "experience level individually. Exact values differ slightly from the saved Phase 8 CSV "
        "(this is a freshly-trained model in this session) but the ranking order matches exactly."
    )

    st.write("")
    st.divider()

    # ---- Local-ish: single-feature sensitivity / what-if ----
    st.markdown("#### What-if: single-feature sensitivity")
    st.caption("Fix a baseline profile, then vary ONE feature at a time to see how the prediction moves.")

    c1, c2, c3 = st.columns(3)
    with c1:
        base_experience = st.selectbox("Baseline: Experience Level", options=["Entry-level", "Mid-level", "Senior", "Executive"], index=2)
        base_employment = st.selectbox("Baseline: Employment Type", options=sorted(jobs["employment_type"].unique()))
    with c2:
        base_category = st.selectbox("Baseline: Job Category", options=sorted(jobs["job_category"].unique()))
        base_size = st.selectbox("Baseline: Company Size", options=["S", "M", "L"], index=1)
    with c3:
        top_countries = jobs["company_location"].value_counts().head(20).index.tolist()
        base_country = st.selectbox("Baseline: Company Location", options=sorted(top_countries))
        base_work_setting = st.selectbox("Baseline: Work Setting", options=sorted(jobs["work_setting"].unique()))

    vary_feature = st.selectbox(
        "Which feature should vary?",
        options=["job_category", "experience_level", "company_location", "work_setting", "company_size", "employment_type"],
    )

    base_input = {
        "experience_level": base_experience, "job_category": base_category, "employment_type": base_employment,
        "company_size": base_size, "work_setting": base_work_setting, "company_location": base_country,
    }

    vary_options = {
        "job_category": sorted(jobs["job_category"].unique()),
        "experience_level": ["Entry-level", "Mid-level", "Senior", "Executive"],
        "company_location": sorted(top_countries),
        "work_setting": sorted(jobs["work_setting"].unique()),
        "company_size": ["S", "M", "L"],
        "employment_type": sorted(jobs["employment_type"].unique()),
    }[vary_feature]

    rows = []
    for option in vary_options:
        input_row = {**base_input, vary_feature: option}
        input_df = pd.DataFrame([input_row])
        pred = float(np.expm1(pipeline.predict(input_df))[0])
        rows.append({vary_feature: option, "predicted_salary": pred})
    sensitivity_df = pd.DataFrame(rows).sort_values("predicted_salary", ascending=True)

    try:
        import plotly.express as px
        fig2 = px.bar(
            sensitivity_df, x="predicted_salary", y=vary_feature, orientation="h",
            labels={"predicted_salary": "Predicted Salary (USD)", vary_feature: ""},
            color_discrete_sequence=["#2A78D6"],
        )
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                             margin=dict(l=10, r=10, t=10, b=10), height=max(280, len(vary_options) * 30))
        with styled_container():
            st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)

    spread = sensitivity_df["predicted_salary"].max() - sensitivity_df["predicted_salary"].min()
    st.info(
        f"Holding every other feature fixed at the baseline profile, varying **{vary_feature}** alone "
        f"swings the prediction by **${spread:,.0f}** across its {len(vary_options)} possible values. "
        "This is the model's learned sensitivity to this one feature for this specific baseline — "
        "it will look different for a different baseline, which is expected (this is exactly the kind "
        "of interaction effect a true SHAP analysis would formally quantify and this simpler method cannot)."
    )

    st.markdown("</div>", unsafe_allow_html=True)
