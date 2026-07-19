"""
Salary Prediction -- the first page in the app with a genuinely live
ML model, not precomputed results. Trains a RandomForestRegressor
(identical methodology to the main project's Phase 8) via
st.cache_resource, so training happens once per server process rather
than on every user interaction.

(Mapped from the original spec's "Funding prediction" -- this project
predicts salary, not funding amounts. See config/settings.py.)

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

FEATURES = ["experience_level", "job_category", "employment_type", "company_size", "work_setting", "company_location"]


@st.cache_resource(show_spinner="Training salary prediction model (one-time, cached)...")
def train_model(_jobs: pd.DataFrame):
    """
    Leading underscore on _jobs tells st.cache_resource not to hash the
    (large) DataFrame as part of the cache key -- st.cache_resource is
    meant for unhashable/expensive objects like a fitted model, and
    hashing a 14k-row DataFrame on every call would be wasteful. This
    means the model retrains only when the app restarts, not when the
    data changes within a session -- correct for this use case, since
    the underlying CSV is static within a deployment.
    """
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_absolute_error, r2_score

    X = _jobs[FEATURES]
    y_log = np.log1p(_jobs["salary_in_usd"])
    y_raw = _jobs["salary_in_usd"]

    X_train, X_test, y_train_log, y_test_log, y_train_raw, y_test_raw = train_test_split(
        X, y_log, y_raw, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES)])
    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
    ])
    pipeline.fit(X_train, y_train_log)

    pred_log = pipeline.predict(X_test)
    pred = np.expm1(pred_log)
    mae = mean_absolute_error(y_test_raw, pred)
    r2 = r2_score(y_test_raw, pred)

    # Residuals -- used to build an honest, data-driven prediction range
    # rather than an arbitrary +/- percentage
    residuals = y_test_raw.values - pred

    return {
        "pipeline": pipeline, "mae": mae, "r2": r2, "residuals": residuals,
        "X_test": X_test, "y_test_log": y_test_log, "y_test_raw": y_test_raw,
    }


@handle_errors("Salary Prediction")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("💰 Salary Prediction")
    st.caption(
        "A live-trained Random Forest model — identical methodology to the main project's "
        "Phase 8 (see reports/ml_analysis.md). Predicts salary from role and location features."
    )

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available -- cannot train a model.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    model_info = train_model(jobs)
    pipeline = model_info["pipeline"]

    st.info(
        f"ℹ️ **Model performance (held-out test set): R² = {model_info['r2']:.3f}, "
        f"MAE = ${model_info['mae']:,.0f}.** This model explains roughly "
        f"{model_info['r2']*100:.0f}% of salary variance — meaning **most of the variation "
        f"in real salaries comes from factors this model doesn't see** (specific company, "
        f"negotiation, cost of living, exact title). Treat every prediction below as a "
        f"reasonable estimate, not a precise figure. See `reports/ml_analysis.md` for full caveats."
    )

    st.write("")
    st.markdown("#### Enter role details")

    c1, c2, c3 = st.columns(3)
    with c1:
        experience_level = st.selectbox("Experience Level", options=["Entry-level", "Mid-level", "Senior", "Executive"])
        employment_type = st.selectbox("Employment Type", options=sorted(jobs["employment_type"].unique()))
    with c2:
        job_category = st.selectbox("Job Category", options=sorted(jobs["job_category"].unique()))
        company_size = st.selectbox("Company Size", options=["S", "M", "L"])
    with c3:
        work_setting = st.selectbox("Work Setting", options=sorted(jobs["work_setting"].unique()))
        top_countries = jobs["company_location"].value_counts().head(20).index.tolist()
        company_location = st.selectbox("Company Location", options=sorted(top_countries))

    predict_clicked = st.button("🔮 Predict Salary", type="primary", use_container_width=True)

    if predict_clicked:
        input_df = pd.DataFrame([{
            "experience_level": experience_level, "job_category": job_category,
            "employment_type": employment_type, "company_size": company_size,
            "work_setting": work_setting, "company_location": company_location,
        }])
        pred_log = pipeline.predict(input_df)
        pred = float(np.expm1(pred_log)[0])

        # Data-driven range from held-out residuals (25th-75th percentile of
        # actual prediction error) rather than an arbitrary +/- X% guess
        residuals = model_info["residuals"]
        low = pred + np.percentile(residuals, 25)
        high = pred + np.percentile(residuals, 75)

        st.write("")
        st.session_state["last_salary_prediction"] = pred  # session_state demo: persists across reruns

        k1, k2, k3 = st.columns(3)
        with k1:
            kpi_card("Predicted Salary", f"${pred:,.0f}", gradient=2)
        with k2:
            kpi_card("Likely Range (IQR of residuals)", f"${low:,.0f} – ${high:,.0f}", gradient=1)
        with k3:
            # Percentile within the actual historical distribution for this category
            cat_jobs = jobs[jobs["job_category"] == job_category]
            if len(cat_jobs) >= 10:
                percentile = (cat_jobs["salary_in_usd"] <= pred).mean() * 100
                kpi_card(f"Percentile within {job_category}", f"{percentile:.0f}th", gradient=3)
            else:
                kpi_card("Category sample size", f"n={len(cat_jobs)}", gradient=3, delta="too small for percentile")

        st.caption(
            "The 'Likely Range' comes from the actual distribution of this model's prediction "
            "errors on held-out real data (25th-75th percentile of residuals) — not a formal "
            "statistical prediction interval, but a more honest range than a guessed +/-percentage."
        )

    st.write("")
    st.divider()
    st.markdown("#### Feature importance (from Phase 8's permutation analysis)")
    st.caption(
        "This live model uses the same features as Phase 8's saved analysis. Permutation "
        "importance (which feature matters most) isn't recomputed live here -- see the "
        "**Model Explainability** page for the full breakdown."
    )
    importance_preview = pd.DataFrame({
        "Feature": ["company_location", "job_category", "experience_level", "work_setting", "company_size", "employment_type"],
        "Relative Importance": [0.296, 0.207, 0.191, 0.011, 0.007, 0.0001],
    })
    try:
        import plotly.express as px
        fig = px.bar(
            importance_preview.sort_values("Relative Importance"), x="Relative Importance", y="Feature",
            orientation="h", color_discrete_sequence=["#4A3AA7"],
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=10, r=10, t=10, b=10), height=280)
        with styled_container():
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.dataframe(importance_preview, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
