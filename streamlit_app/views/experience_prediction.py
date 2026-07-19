"""
Experience-Level Prediction -- live classification model.

IMPORTANT: this page uses a CORRECTED version of the main project's
Phase 8 classification pipeline. While porting that page's methodology
here, comparing this live model's output against Phase 8's reported
metrics surfaced a real bug in the original script
(src/ml/classification_models.py): salary_in_usd was listed as an
intended feature in both the code's `features` list and in
reports/ml_analysis.md's methodology section, but the ColumnTransformer
had no `remainder="passthrough"`, so scikit-learn's default
(remainder='drop') silently discarded it. The original model was
trained on 90 one-hot columns with salary completely absent.

This page fixes that (remainder="passthrough" below) and reports the
corrected metrics. The main project's src/ml/classification_models.py
and reports/ml_analysis.md still have the original bug as of this
build -- see the caption below and the conversation for the fix
recommendation.

(Mapped from the original spec's "Success prediction" -- this project
predicts experience level, not startup success. See config/settings.py.)

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import load_jobs
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container

CAT_FEATURES = ["job_category", "employment_type", "company_size", "work_setting", "company_location"]
ALL_FEATURES = CAT_FEATURES + ["salary_in_usd"]
CLASS_ORDER = ["Entry-level", "Mid-level", "Senior", "Executive"]


@st.cache_resource(show_spinner="Training experience-level classifier (one-time, cached)...")
def train_model(_jobs: pd.DataFrame):
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import classification_report, accuracy_score, f1_score

    X = _jobs[ALL_FEATURES]
    y = _jobs["experience_level"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # THE FIX: remainder="passthrough" so salary_in_usd actually reaches the model
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES)],
        remainder="passthrough",
    )
    pipeline = Pipeline([("preprocess", preprocessor), ("model", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1))])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)

    return {"pipeline": pipeline, "accuracy": acc, "f1": f1, "report": report}


@handle_errors("Experience-Level Prediction")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("🎯 Experience-Level Prediction")
    st.caption(
        "Live-trained classifier predicting experience level from role, location, and salary. "
        "See the bug-fix note below before trusting the headline accuracy."
    )

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No job postings data available -- cannot train a model.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.expander("🐛 A bug was found and fixed while building this page", expanded=True):
        st.markdown(
            "The main project's Phase 8 classification script listed `salary_in_usd` as a "
            "feature, but a missing `remainder=\"passthrough\"` on the `ColumnTransformer` "
            "silently dropped it (scikit-learn's default is to drop unlisted columns). "
            "The original model was trained **without salary at all**, despite the "
            "documentation saying otherwise. This page uses the corrected pipeline. "
            "Recommendation: patch `src/ml/classification_models.py` and "
            "`reports/ml_analysis.md` in the main project to match."
        )

    model_info = train_model(jobs)
    report = model_info["report"]

    st.write("")
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Accuracy (corrected)", f"{model_info['accuracy']:.1%}", gradient=1,
                  delta=f"was {0.676:.1%} before fix")
    with k2:
        kpi_card("Weighted F1 (corrected)", f"{model_info['f1']:.3f}", gradient=2,
                  delta=f"was {0.596:.3f} before fix")
    with k3:
        entry_recall = report.get("Entry-level", {}).get("recall", 0)
        kpi_card("Entry-level Recall", f"{entry_recall:.1%}", gradient=3, delta="was 9% before fix")

    st.markdown("##### Per-class performance (still uneven, but meaningfully improved)")
    per_class = pd.DataFrame({
        cls: {"Precision": report[cls]["precision"], "Recall": report[cls]["recall"], "F1": report[cls]["f1-score"], "Support": int(report[cls]["support"])}
        for cls in CLASS_ORDER if cls in report
    }).T
    st.dataframe(
        per_class.style.format({"Precision": "{:.2f}", "Recall": "{:.2f}", "F1": "{:.2f}", "Support": "{:.0f}"}),
        use_container_width=True,
    )
    st.caption(
        "Senior still has the highest recall (largest class, 66% of the dataset) — this "
        "is genuinely still an imbalanced-classes situation, just less severe than "
        "originally reported. Executive remains the hardest class to predict (smallest sample)."
    )

    st.write("")
    st.divider()

    st.markdown("#### Try a prediction")
    c1, c2, c3 = st.columns(3)
    with c1:
        job_category = st.selectbox("Job Category", options=sorted(jobs["job_category"].unique()), key="exp_cat")
        employment_type = st.selectbox("Employment Type", options=sorted(jobs["employment_type"].unique()), key="exp_emp")
    with c2:
        company_size = st.selectbox("Company Size", options=["S", "M", "L"], key="exp_size")
        work_setting = st.selectbox("Work Setting", options=sorted(jobs["work_setting"].unique()), key="exp_work")
    with c3:
        top_countries = jobs["company_location"].value_counts().head(20).index.tolist()
        company_location = st.selectbox("Company Location", options=sorted(top_countries), key="exp_country")
        salary_in_usd = st.number_input("Salary (USD)", min_value=15000, max_value=450000, value=140000, step=5000, key="exp_salary")

    if st.button("🔮 Predict Experience Level", type="primary", use_container_width=True):
        input_df = pd.DataFrame([{
            "job_category": job_category, "employment_type": employment_type, "company_size": company_size,
            "work_setting": work_setting, "company_location": company_location, "salary_in_usd": salary_in_usd,
        }])
        pipeline = model_info["pipeline"]
        proba = pipeline.predict_proba(input_df)[0]
        classes = pipeline.classes_
        pred_class = classes[np.argmax(proba)]

        st.write("")
        kpi_card("Predicted Experience Level", pred_class, gradient=2, delta=f"{proba.max():.0%} confidence")

        st.write("")
        st.markdown("##### Full probability distribution across all classes")
        proba_df = pd.DataFrame({"Experience Level": classes, "Probability": proba}).sort_values("Probability", ascending=True)
        try:
            import plotly.express as px
            fig = px.bar(proba_df, x="Probability", y="Experience Level", orientation="h",
                         color_discrete_sequence=["#2A78D6"])
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=10, r=10, t=10, b=10), height=250, xaxis_tickformat=".0%")
            with styled_container():
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.dataframe(proba_df, use_container_width=True, hide_index=True)

        st.caption(
            "Showing the full probability distribution, not just the top prediction, is "
            "deliberate — given this model's known class-imbalance behavior, a single "
            "predicted label can hide how uncertain the model actually is."
        )

    st.markdown("</div>", unsafe_allow_html=True)
