"""
Cleans survey_results_public.csv (Stack Overflow 2024 Developer Survey).
Author: Md Imamuddin

Real survey data, 65,437 respondents x 114 columns. License: ODbL --
attribution required (see docs/data_sources.md).

Key decisions:
  1. Only a relevant subset of the 114 columns is carried forward.
     The full survey covers everything from IDE preferences to AI
     sentiment; our platform cares about role, compensation, location,
     experience, education, and tech-stack (skills) columns. Dropping
     the rest isn't data loss -- it's scope discipline. The raw file
     stays untouched in data/raw if anyone needs the full survey later.
  2. Two outputs, not one:
       - so_skills.csv   : every respondent, for NLP/skills-demand analysis
                            (doesn't require compensation to be useful)
       - so_salary.csv    : only respondents with a non-null, converted USD
                            compensation figure. Comp is optional in the
                            survey (64% null) -- silently keeping nulls in
                            a "salary" table would corrupt every salary
                            aggregate downstream.
  3. ConvertedCompYearly has extreme outliers ($1 to $16.2M) -- almost
     certainly including joke/test responses at the low end. Flagged,
     and additionally we hard-floor at $1,000/yr as a sanity floor
     (documented, not silently dropped -- rows are kept with a flag).
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger
from utils.data_quality import flag_outliers, null_report

logger = get_logger("clean_so_survey")

RAW_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "survey_results_public.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

RELEVANT_COLUMNS = [
    "ResponseId", "Country", "EdLevel", "YearsCodePro", "DevType", "Employment",
    "RemoteWork", "OrgSize", "Industry", "Currency", "CompTotal", "ConvertedCompYearly",
    "LanguageHaveWorkedWith", "DatabaseHaveWorkedWith", "PlatformHaveWorkedWith",
    "WebframeHaveWorkedWith", "ToolsTechHaveWorkedWith",
]


def load_raw() -> pd.DataFrame:
    logger.info(f"Loading raw file: {RAW_PATH} (subset of columns only)")
    df = pd.read_csv(RAW_PATH, usecols=RELEVANT_COLUMNS,encoding="utf-8-sig")
    logger.info(f"Loaded shape: {df.shape}")
    return df


def build_skills_view(df: pd.DataFrame) -> pd.DataFrame:
    """Every respondent -- used for skills/tech-stack demand analysis (NLP module)."""
    skills_df = df.copy()
    skills_df["source_dataset"] = "stackoverflow_2024"
    return skills_df


def build_salary_view(df: pd.DataFrame) -> pd.DataFrame:
    """Only respondents with usable compensation data."""
    salary_df = df.dropna(subset=["ConvertedCompYearly", "Country"]).copy()
    logger.info(
        f"Salary view: kept {len(salary_df)} / {len(df)} rows "
        f"({len(salary_df)/len(df)*100:.1f}%) with non-null comp + country"
    )

    # Sanity floor: comp below $1,000/yr is almost certainly a data-entry
    # error or joke response, not a real annual salary. Kept, but flagged
    # rather than dropped, so nothing is silently destroyed.
    salary_df["below_sanity_floor"] = salary_df["ConvertedCompYearly"] < 1000
    n_floor = salary_df["below_sanity_floor"].sum()
    logger.info(f"Rows below $1,000/yr sanity floor: {n_floor}")

    salary_df = flag_outliers(salary_df, "ConvertedCompYearly", flag_col="comp_is_outlier")
    salary_df["source_dataset"] = "stackoverflow_2024"
    return salary_df


def main():
    df = load_raw()
    nulls = null_report(df)
    logger.info(f"Null report (top 8):\n{nulls.head(8)}")

    skills_view = build_skills_view(df)
    salary_view = build_salary_view(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    skills_path = OUT_DIR / "so_skills_clean.csv"
    salary_path = OUT_DIR / "so_salary_clean.csv"
    skills_view.to_csv(skills_path, index=False,encoding="utf-8-sig")
    salary_view.to_csv(salary_path, index=False,encoding="utf-8-sig")

    logger.info(f"Wrote skills view: {skills_path} shape={skills_view.shape}")
    logger.info(f"Wrote salary view: {salary_path} shape={salary_view.shape}")

    return skills_view, salary_view


if __name__ == "__main__":
    main()
