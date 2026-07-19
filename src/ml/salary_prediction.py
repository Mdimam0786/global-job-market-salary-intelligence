"""
Phase 8 -- ML Model 1: Salary Prediction
Author: Md Imamuddin

Tooling note: xgboost, lightgbm, and shap weren't available, so gradient
boosting is done with scikit-learn's GradientBoostingRegressor instead of
XGBoost/LightGBM -- same algorithm family, slower and less tunable at scale, but directly
comparable in output. In place of SHAP, this script uses scikit-learn's
permutation_importance, which answers a similar question ("how much does
shuffling this feature hurt model performance") at the global level, but
does NOT provide per-prediction Shapley values or interaction effects --
that's a genuine capability gap versus SHAP, not a drop-in replacement,
and is reported as a limitation rather than papered over.

Per the Phase 7 distribution analysis, salary is log-transformed before
fitting the linear model (tree-based models are less sensitive to this
but log-transforming doesn't hurt them either, so it's applied uniformly
for a fair comparison across model types).
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold, RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.inspection import permutation_importance

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("salary_prediction")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MODEL_DIR = Path(__file__).resolve().parents[2] / "reports"

FEATURES_NUM = []
FEATURES_CAT = ["experience_level", "job_category", "employment_type", "company_size",
                "work_setting", "company_location"]
TARGET = "salary_in_usd"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "jobs_fact_clean.csv")
    logger.info(f"Loaded {df.shape[0]} rows for salary prediction")
    return df


def build_pipeline(model):
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES_CAT),
    ])
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def evaluate(name, pipeline, X_train, X_test, y_train_log, y_test_log, y_test_raw):
    pipeline.fit(X_train, y_train_log)
    pred_log = pipeline.predict(X_test)
    pred = np.expm1(pred_log)

    mae = mean_absolute_error(y_test_raw, pred)
    rmse = np.sqrt(mean_squared_error(y_test_raw, pred))
    r2 = r2_score(y_test_raw, pred)

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train_log, cv=cv, scoring="r2")

    logger.info(f"{name}: MAE=${mae:,.0f}  RMSE=${rmse:,.0f}  R2(test)={r2:.3f}  "
                f"5-fold CV R2={cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    return {"name": name, "mae": mae, "rmse": rmse, "r2": r2, "cv_r2_mean": cv_scores.mean(), "cv_r2_std": cv_scores.std()}


def hyperparameter_tuning(X_train, y_train_log):
    logger.info("Hyperparameter tuning: RandomizedSearchCV over GradientBoostingRegressor")
    param_dist = {
        "model__n_estimators": [100, 200, 300],
        "model__max_depth": [2, 3, 4, 5],
        "model__learning_rate": [0.01, 0.05, 0.1],
        "model__subsample": [0.7, 0.85, 1.0],
    }
    pipeline = build_pipeline(GradientBoostingRegressor(random_state=42))
    search = RandomizedSearchCV(
        pipeline, param_dist, n_iter=15, cv=3, scoring="r2",
        random_state=42, n_jobs=-1,
    )
    search.fit(X_train, y_train_log)
    logger.info(f"Best params: {search.best_params_}")
    logger.info(f"Best CV R2: {search.best_score_:.3f}")
    return search.best_estimator_, search.best_params_


def explainability(best_pipeline, X_test, y_test_log):
    logger.info("Permutation importance (global feature importance, SHAP substitute -- see module docstring)")
    # Note: permutation_importance operates on the full pipeline, so it shuffles
    # the RAW input columns (FEATURES_CAT), not the expanded one-hot columns --
    # each original categorical column gets a single importance score directly.
    result = permutation_importance(best_pipeline, X_test, y_test_log, n_repeats=10, random_state=42, n_jobs=-1)
    col_importance = pd.Series(result.importances_mean, index=X_test.columns).sort_values(ascending=False)
    logger.info(f"Feature importance by column (permutation-based):\n{col_importance}")
    return col_importance


def main():
    df = load_data()
    X = df[FEATURES_CAT]
    y_raw = df[TARGET]
    y_log = np.log1p(y_raw)

    X_train, X_test, y_train_log, y_test_log, y_train_raw, y_test_raw = train_test_split(
        X, y_log, y_raw, test_size=0.2, random_state=42
    )

    results = []
    results.append(evaluate("Linear Regression", build_pipeline(LinearRegression()),
                             X_train, X_test, y_train_log, y_test_log, y_test_raw))
    results.append(evaluate("Random Forest", build_pipeline(RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
                             X_train, X_test, y_train_log, y_test_log, y_test_raw))
    results.append(evaluate("Gradient Boosting (default)", build_pipeline(GradientBoostingRegressor(random_state=42)),
                             X_train, X_test, y_train_log, y_test_log, y_test_raw))

    best_pipeline, best_params = hyperparameter_tuning(X_train, y_train_log)
    pred_log = best_pipeline.predict(X_test)
    pred = np.expm1(pred_log)
    tuned_r2 = r2_score(y_test_raw, pred)
    tuned_mae = mean_absolute_error(y_test_raw, pred)
    logger.info(f"Tuned Gradient Boosting: MAE=${tuned_mae:,.0f}  R2(test)={tuned_r2:.3f}")
    results.append({"name": "Gradient Boosting (tuned)", "mae": tuned_mae, "rmse": None,
                     "r2": tuned_r2, "cv_r2_mean": None, "cv_r2_std": None})

    col_importance = explainability(best_pipeline, X_test, y_test_log)

    comparison_df = pd.DataFrame(results)
    comparison_df.to_csv(MODEL_DIR / "salary_model_comparison.csv", index=False)
    col_importance.to_csv(MODEL_DIR / "salary_feature_importance.csv", header=["importance"])
    logger.info(f"Wrote model comparison and feature importance to {MODEL_DIR}")

    return comparison_df, col_importance, best_params


if __name__ == "__main__":
    main()
