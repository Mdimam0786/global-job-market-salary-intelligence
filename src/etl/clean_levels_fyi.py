"""
Cleans Levels_Fyi_Salary_Data.csv (company/level compensation benchmarking source).
Author: Md Imamuddin

Real self-reported data, 62,642 rows x 29 columns. Big-Tech-heavy
(Amazon/Microsoft/Google/Facebook/Apple dominate), so treated as a
company-benchmarking dimension, not blended into the primary
jobs_in_data_2024 fact table (different populations, different
collection methodology -- merging them would misrepresent both).

Key decisions:
  1. `location` is "City, State" for US rows and "City, Region, Country"
     for international rows. Parsed into city/region/country with a
     rule-based approach (comma count) rather than a lookup table --
     documented and testable, not a black box.
  2. gender and Race are heavily null (31% / 64%) because they're
     optional self-reported survey fields. We do NOT impute these --
     imputing demographic data would fabricate information about real
     people. Nulls are kept as-is and any demographic chart must state
     the reduced sample size.
  3. totalyearlycompensation has a legitimate long right tail (staff+
     engineers, heavy equity). Outliers are flagged, not dropped.
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger
from utils.data_quality import flag_outliers, null_report, duplicate_report

logger = get_logger("clean_levels_fyi")

RAW_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "Levels_Fyi_Salary_Data.csv"
OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "levels_fyi_clean.csv"

US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


def load_raw() -> pd.DataFrame:
    logger.info(f"Loading raw file: {RAW_PATH}")
    df = pd.read_csv(RAW_PATH,encoding="utf-8-sig")
    logger.info(f"Loaded shape: {df.shape}")
    return df


def parse_location(location: str) -> pd.Series:
    """
    'Seattle, WA'                  -> city=Seattle, region=WA, country=United States
    'Amsterdam, NH, Netherlands'   -> city=Amsterdam, region=NH, country=Netherlands
    Falls back gracefully on anything unexpected.
    """
    parts = [p.strip() for p in str(location).split(",")]
    if len(parts) == 2 and parts[1] in US_STATE_CODES:
        return pd.Series({"city": parts[0], "region": parts[1], "country": "United States"})
    if len(parts) == 3:
        return pd.Series({"city": parts[0], "region": parts[1], "country": parts[2]})
    if len(parts) == 1:
        return pd.Series({"city": parts[0], "region": None, "country": None})
    # Unexpected shape (e.g. city names containing commas) -- keep raw, flag for review
    return pd.Series({"city": parts[0], "region": ",".join(parts[1:-1]) or None, "country": parts[-1]})


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    location_parts = df["location"].apply(parse_location)
    df = pd.concat([df, location_parts], axis=1)

    # US is implied (no explicit country token) for ~90% of rows -- verify the split looks sane
    unresolved_country = df["country"].isnull().sum()
    logger.info(f"Rows where country could not be parsed: {unresolved_country}")

    df = flag_outliers(df, "totalyearlycompensation", flag_col="total_comp_is_outlier")

    # Drop the pre-computed demographic dummy columns (Masters_Degree, Race_White, ...)
    # in favor of the single Education / Race columns -- redundant one-hot encodings
    # bloat the table and duplicate information already in Education/Race.
    dummy_cols = [
        "Masters_Degree", "Bachelors_Degree", "Doctorate_Degree", "Highschool",
        "Some_College", "Race_Asian", "Race_White", "Race_Two_Or_More",
        "Race_Black", "Race_Hispanic",
    ]
    df = df.drop(columns=[c for c in dummy_cols if c in df.columns])

    df = df.rename(columns={
        "totalyearlycompensation": "total_yearly_compensation",
        "yearsofexperience": "years_of_experience",
        "yearsatcompany": "years_at_company",
        "basesalary": "base_salary",
        "stockgrantvalue": "stock_grant_value",
    })

    df["source_dataset"] = "levels_fyi"
    df.insert(0, "record_id", range(1, len(df) + 1))

    return df


def main():
    df_raw = load_raw()
    logger.info(f"Duplicate report: {duplicate_report(df_raw)}")
    nulls = null_report(df_raw)
    logger.info(f"Top null columns:\n{nulls.head(8)}")

    df_clean = clean(df_raw)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(OUT_PATH, index=False,encoding="utf-8-sig")
    logger.info(f"Wrote cleaned Levels.fyi table: {OUT_PATH} shape={df_clean.shape}")

    n_outliers = df_clean["total_comp_is_outlier"].sum()
    logger.info(f"Flagged {n_outliers} comp outliers ({n_outliers/len(df_clean)*100:.2f}%)")

    return df_clean


if __name__ == "__main__":
    main()
