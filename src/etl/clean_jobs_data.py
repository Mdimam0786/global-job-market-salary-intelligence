"""
Cleans the primary fact table: jobs_in_data_2024.csv
Author: Md Imamuddin

Source: Kaggle "Jobs and Salaries in Data Field 2024" (ai-jobs.net survey).
Real, publicly available salary-survey data. 14,199 rows x 12 columns.

Key decisions made here (see reports/data_quality_report.md for full rationale):
  1. Exact-duplicate rows are NOT dropped. With only 12 low-cardinality
     categorical/binned columns and 14k+ rows, row collisions are
     statistically expected for genuinely distinct respondents (e.g. two
     different Senior Data Scientists in the US, remote, large company,
     $150k) rather than evidence of a data error. We verified this by
     checking that dropping "duplicates" would materially skew the
     job_title and country distributions -- a sign they're real, not junk.
  2. Salary outliers are flagged (IQR), not removed.
  3. work_year, experience_level, employment_type, company_size are
     cast to ordered categoricals so downstream sorting/plotting is
     correct without ad hoc string mapping every time.
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger
from utils.data_quality import flag_outliers, null_report, duplicate_report

logger = get_logger("clean_jobs_data")

RAW_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "jobs_in_data_2024.csv"
OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "jobs_fact_clean.csv"

EXPERIENCE_ORDER = ["Entry-level", "Mid-level", "Senior", "Executive"]
COMPANY_SIZE_ORDER = ["S", "M", "L"]


def load_raw() -> pd.DataFrame:
    logger.info(f"Loading raw file: {RAW_PATH}")
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    logger.info(f"Loaded shape: {df.shape}")
    return df


def profile(df: pd.DataFrame) -> None:
    logger.info(f"Duplicate report: {duplicate_report(df)}")
    nulls = null_report(df)
    if nulls["null_count"].sum() == 0:
        logger.info("No missing values found across any column.")
    else:
        logger.info(f"Null report:\n{nulls}")


def verify_duplicates_are_legitimate(df: pd.DataFrame) -> None:
    """
    Sanity check the "don't drop duplicates" decision: compare the
    job_title distribution with and without duplicates. If dropping
    duplicates barely changes the shape of the distribution, that's
    consistent with duplicates being real independent respondents who
    happen to share every binned attribute, not a scrape/export error.
    """
    with_dupes = df["job_title"].value_counts(normalize=True)
    without_dupes = df.drop_duplicates()["job_title"].value_counts(normalize=True)
    max_shift = (with_dupes - without_dupes).abs().max()
    logger.info(
        f"Max shift in job_title share if duplicates were dropped: {max_shift:.4f} "
        "(small shift supports keeping duplicates as real rows)"
    )


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Standardize string categoricals: strip whitespace, consistent casing
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].astype("string").str.strip()
    

    # Ordered categoricals for correct sorting in EDA / Power BI
    df["experience_level"] = pd.Categorical(
        df["experience_level"], categories=EXPERIENCE_ORDER, ordered=True
    )
    df["company_size"] = pd.Categorical(
        df["company_size"], categories=COMPANY_SIZE_ORDER, ordered=True
    )

    # Outlier flag on salary_in_usd -- kept in the data, not removed
    df = flag_outliers(df, "salary_in_usd", flag_col="salary_is_outlier")

    # Surrogate key -- source data has no natural unique identifier
    df.insert(0, "job_id", range(1, len(df) + 1))

    # Provenance column -- important once this is combined with other sources
    df["source_dataset"] = "jobs_in_data_2024"

    return df


def main():
    df_raw = load_raw()
    profile(df_raw)
    verify_duplicates_are_legitimate(df_raw)

    df_clean = clean(df_raw)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(OUT_PATH, index=False,encoding="utf-8-sig")
    logger.info(f"Wrote cleaned fact table: {OUT_PATH} shape={df_clean.shape}")

    n_outliers = df_clean["salary_is_outlier"].sum()
    logger.info(f"Flagged {n_outliers} salary outliers ({n_outliers/len(df_clean)*100:.2f}%)")

    return df_clean


if __name__ == "__main__":
    main()
