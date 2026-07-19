"""
Reusable data-quality helpers shared across the ETL scripts.
Author: Md Imamuddin

Design decision: outliers are FLAGGED, not silently dropped. Salary
data legitimately has a long right tail (executives, staff+ engineers,
equity-heavy comp). Dropping those rows would quietly bias the dataset
toward the median and misrepresent the market. Downstream consumers
(EDA, ML, Power BI) decide whether to filter on the flag.
"""

from __future__ import annotations

import pandas as pd


def iqr_outlier_bounds(series: pd.Series, k: float = 1.5) -> tuple[float, float]:
    """Return (lower_bound, upper_bound) using the standard IQR rule."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def flag_outliers(df: pd.DataFrame, column: str, k: float = 1.5,
                   flag_col: str | None = None) -> pd.DataFrame:
    """Add a boolean column flagging IQR outliers in `column`. Non-destructive."""
    flag_col = flag_col or f"{column}_is_outlier"
    lower, upper = iqr_outlier_bounds(df[column].dropna(), k=k)
    df[flag_col] = ~df[column].between(lower, upper)
    return df


def null_report(df: pd.DataFrame) -> pd.DataFrame:
    """Column-level null count + percentage, sorted worst first."""
    nulls = df.isnull().sum()
    pct = (nulls / len(df) * 100).round(2)
    report = pd.DataFrame({"null_count": nulls, "null_pct": pct})
    return report.sort_values("null_pct", ascending=False)


def duplicate_report(df: pd.DataFrame) -> dict:
    """Exact-duplicate-row count and percentage of the dataframe."""
    dup_count = int(df.duplicated().sum())
    return {
        "duplicate_rows": dup_count,
        "duplicate_pct": round(dup_count / len(df) * 100, 2),
        "total_rows": len(df),
    }
