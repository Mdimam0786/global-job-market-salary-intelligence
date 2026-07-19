"""
Phase 8 -- ML Models 2 & 3: Experience Level Prediction, Remote Work Prediction
Author: Md Imamuddin

Both are multi-class classification problems solved with the same
pattern: encode categorical features, compare Logistic Regression vs.
Random Forest, 5-fold cross-validation, classification report.

Design note on leakage: job_title is deliberately EXCLUDED as a feature
for experience-level prediction, even though titles often literally
contain "Senior"/"Junior" -- including it would make the task trivial
string matching, not a genuine prediction problem, and would produce a
model that's useless on any title that doesn't follow that convention.
"""

from pathlib import Path
import sys

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, f1_score

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("classification_models")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def build_pipeline(model, cat_features):
    # BUG FIX (found while porting this to the Streamlit companion app):
    # remainder="passthrough" is required so that any feature NOT in
    # cat_features (i.e. salary_in_usd) actually reaches the model.
    # Without it, ColumnTransformer's default remainder='drop' silently
    # discards salary_in_usd even though it's listed in `features` below --
    # the original version of this function trained on categorical
    # features ONLY, despite salary being intended as a predictor.
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)],
        remainder="passthrough",
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def run_classification_task(task_name, df, features, target, cat_features):
    logger.info("=" * 70)
    logger.info(f"TASK: {task_name}")
    logger.info("=" * 70)

    X = df[features]
    y = df[target]
    logger.info(f"Class distribution:\n{y.value_counts()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = []
    for name, model in [
        ("Logistic Regression", LogisticRegression(max_iter=1000)),
        ("Random Forest", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)),
    ]:
        pipeline = build_pipeline(model, cat_features)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_weighted")

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")

        logger.info(f"{name}: test accuracy={acc:.3f}, weighted F1={f1:.3f}, "
                    f"5-fold CV weighted F1={cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        results.append({"model": name, "accuracy": acc, "f1_weighted": f1,
                         "cv_f1_mean": cv_scores.mean(), "cv_f1_std": cv_scores.std()})

    logger.info(f"Detailed classification report (Random Forest):\n"
                f"{classification_report(y_test, pipeline.predict(X_test))}")

    return pd.DataFrame(results)


def main():
    jobs = pd.read_csv(DATA_DIR / "jobs_fact_clean.csv")

    # Task 1: Experience level prediction (job_title deliberately excluded -- see docstring)
    exp_features = ["job_category", "employment_type", "company_size", "work_setting",
                     "company_location", "salary_in_usd"]
    exp_cat = ["job_category", "employment_type", "company_size", "work_setting", "company_location"]
    exp_results = run_classification_task(
        "Experience Level Prediction", jobs, exp_features, "experience_level", exp_cat
    )

    # Task 2: Remote work status prediction
    remote_features = ["job_category", "experience_level", "employment_type", "company_size",
                        "company_location", "salary_in_usd"]
    remote_cat = ["job_category", "experience_level", "employment_type", "company_size", "company_location"]
    remote_results = run_classification_task(
        "Remote Work Status Prediction", jobs, remote_features, "work_setting", remote_cat
    )

    exp_results.to_csv(Path(__file__).resolve().parents[2] / "reports" / "experience_level_model_comparison.csv", index=False)
    remote_results.to_csv(Path(__file__).resolve().parents[2] / "reports" / "remote_work_model_comparison.csv", index=False)

    return exp_results, remote_results


if __name__ == "__main__":
    main()
