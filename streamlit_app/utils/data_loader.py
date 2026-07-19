"""
Cached data loaders. Every function uses st.cache_data so the CSVs are
read from disk once per app session (or until the underlying file
changes / TTL expires), not on every single widget interaction --
Streamlit reruns the whole script top-to-bottom on every click, so
without caching this would re-read a multi-thousand-row CSV from disk
dozens of times in a normal user session.

DATABASE TOGGLE: set USE_DATABASE=true in .env to read from a live
PostgreSQL instance instead of the bundled CSVs (see
database/load_data.py to populate it first). Default is CSV -- the
app works with zero setup unless you opt into the database. See
utils/db_loader.py for the Postgres-backed equivalents of these
functions.

Author: Md Imamuddin
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from config.settings import DATA_DIR, REPORTS_DIR, FILES, REPORT_FILES
from utils.logger import get_logger

load_dotenv()  # no-op if no .env file exists -- safe to call unconditionally

logger = get_logger(__name__)

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

if USE_DATABASE:
    logger.info("USE_DATABASE=true -- data will be read from PostgreSQL, not bundled CSVs")


def _safe_read_csv(path, label: str) -> pd.DataFrame:
    """Shared read logic: log + return an empty DataFrame on failure
    rather than raising, so one missing file degrades that one page's
    functionality instead of crashing the whole app on first load."""
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {label}: {df.shape[0]} rows x {df.shape[1]} cols from {path}")
        return df
    except FileNotFoundError:
        logger.error(f"Data file not found for '{label}': {path}")
        st.warning(
            f"Data file for **{label}** wasn't found at `{path}`. "
            "This page will show limited/no data until it's added -- "
            "see README.md's data setup instructions."
        )
        return pd.DataFrame()
    except Exception as exc:
        logger.error(f"Unexpected error loading '{label}' from {path}: {exc}")
        st.warning(f"Couldn't load **{label}** -- see logs for details.")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner="Loading job postings data...")
def load_jobs() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_jobs as db_load_jobs
        return db_load_jobs()
    return _safe_read_csv(DATA_DIR / FILES["jobs"], "Job Postings")


@st.cache_data(ttl=3600, show_spinner="Loading company compensation data...")
def load_levels() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_levels as db_load_levels
        return db_load_levels()
    return _safe_read_csv(DATA_DIR / FILES["levels"], "Company Compensation (Levels.fyi)")


@st.cache_data(ttl=3600, show_spinner="Loading survey salary data...")
def load_so_salary() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_so_salary as db_load_so_salary
        return db_load_so_salary()
    return _safe_read_csv(DATA_DIR / FILES["so_salary"], "Developer Survey Salaries")


@st.cache_data(ttl=3600, show_spinner="Loading skills data...")
def load_so_skills() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_so_skills as db_load_so_skills
        return db_load_so_skills()
    return _safe_read_csv(DATA_DIR / FILES["so_skills"], "Developer Skills Survey")


@st.cache_data(ttl=3600)
def load_dim_skill() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_dim_skill as db_load_dim_skill
        return db_load_dim_skill()
    return _safe_read_csv(DATA_DIR / FILES["dim_skill"], "Skill Dimension")


@st.cache_data(ttl=3600)
def load_skill_bridge() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_skill_bridge as db_load_skill_bridge
        return db_load_skill_bridge()
    return _safe_read_csv(DATA_DIR / FILES["skill_bridge"], "Skill Bridge Table")


@st.cache_data(ttl=3600)
def load_skill_rules() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_skill_rules as db_load_skill_rules
        return db_load_skill_rules()
    return _safe_read_csv(DATA_DIR / FILES["skill_rules"], "Skill Association Rules")


@st.cache_data(ttl=3600)
def load_job_clusters() -> pd.DataFrame:
    if USE_DATABASE:
        from utils.db_loader import load_job_clusters as db_load_job_clusters
        return db_load_job_clusters()
    return _safe_read_csv(DATA_DIR / FILES["job_clusters"], "Job Clusters")


@st.cache_data(ttl=3600)
def load_model_comparison() -> pd.DataFrame:
    # Static ML report output -- always read from CSV, no database
    # equivalent (these are saved model results, not live queryable data)
    return _safe_read_csv(REPORTS_DIR / REPORT_FILES["model_comparison"], "Model Comparison")


@st.cache_data(ttl=3600)
def load_feature_importance() -> pd.DataFrame:
    return _safe_read_csv(REPORTS_DIR / REPORT_FILES["feature_importance"], "Feature Importance")


@st.cache_data(ttl=3600, show_spinner="Computing summary KPIs...")
def compute_home_kpis() -> dict:
    """One consolidated cached call for the Home page's KPI cards --
    avoids the Home page separately loading+aggregating multiple full
    tables on every render just to show 4 numbers."""
    jobs = load_jobs()
    if jobs.empty:
        return {"total_postings": 0, "avg_salary": 0, "company_locations": 0, "remote_pct": 0.0}

    return {
        "total_postings": len(jobs),
        "avg_salary": round(jobs["salary_in_usd"].mean()) if "salary_in_usd" in jobs else 0,
        "company_locations": jobs["company_location"].nunique() if "company_location" in jobs else 0,
        "remote_pct": round((jobs["work_setting"] == "Remote").mean() * 100, 1)
        if "work_setting" in jobs
        else 0.0,
    }
