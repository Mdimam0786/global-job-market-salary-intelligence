"""
utils/db_loader.py

PostgreSQL-backed equivalents of utils/data_loader.py's CSV loaders.
Only used if DATABASE_URL is set AND USE_DATABASE=true in your
environment (see .env.example) -- otherwise the app reads the bundled
CSVs directly and this module is never imported. This keeps the
zero-setup CSV experience as the default; Postgres is opt-in.

Requires: sqlalchemy, psycopg2-binary (NOT in the default
requirements.txt -- see requirements-database.txt).

Author: Md Imamuddin
"""

import os

import pandas as pd
import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


@st.cache_resource
def get_engine():
    """Cached so the connection pool is created once per server
    process, not reconnected on every query."""
    from sqlalchemy import create_engine

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to your .env file, or set "
            "USE_DATABASE=false to use the bundled CSVs instead."
        )
    return create_engine(database_url, pool_pre_ping=True)


def _safe_query(query: str, label: str, csv_filename: str = None) -> pd.DataFrame:
    try:
        engine = get_engine()
        df = pd.read_sql(query, engine)
        logger.info(f"Loaded {label} from database: {df.shape[0]} rows")
        return df
    except Exception as exc:
        logger.error(f"Database query failed for '{label}': {exc}")
        st.error(
            f"Couldn't load **{label}** from the database. Check that "
            "PostgreSQL is running, DATABASE_URL is correct, and "
            "`python scripts/load_star_schema.py` (run from the repo root) has been "
            "run. Falling back "
            "to bundled CSV data for this table."
        )
        # IMPORTANT: fall back by reading the CSV directly, NOT by calling
        # data_loader.py's public load_*() functions. Those functions
        # check USE_DATABASE and would route straight back into this
        # module, causing infinite recursion if the DB connection keeps
        # failing. Reading the CSV directly here breaks that loop.
        if csv_filename:
            from config.settings import DATA_DIR
            try:
                return pd.read_csv(DATA_DIR / csv_filename)
            except FileNotFoundError:
                logger.error(f"CSV fallback also not found: {DATA_DIR / csv_filename}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner="Loading job postings from database...")
def load_jobs() -> pd.DataFrame:
    return _safe_query("SELECT * FROM fact_job_postings", "Job Postings", "jobs_fact_clean.csv")


@st.cache_data(ttl=3600, show_spinner="Loading company compensation from database...")
def load_levels() -> pd.DataFrame:
    return _safe_query("SELECT * FROM fact_levels_compensation", "Company Compensation", "levels_fyi_clean.csv")


@st.cache_data(ttl=3600, show_spinner="Loading survey salary data from database...")
def load_so_salary() -> pd.DataFrame:
    return _safe_query("SELECT * FROM fact_so_respondent", "Developer Survey Salaries", "so_salary_clean.csv")


@st.cache_data(ttl=3600)
def load_so_skills() -> pd.DataFrame:
    return _safe_query("SELECT * FROM fact_so_skills_survey", "Developer Skills Survey", "so_skills_clean.csv")


@st.cache_data(ttl=3600)
def load_dim_skill() -> pd.DataFrame:
    return _safe_query("SELECT * FROM dim_skill", "Skill Dimension", "dim_skill.csv")


@st.cache_data(ttl=3600)
def load_skill_bridge() -> pd.DataFrame:
    return _safe_query("SELECT * FROM bridge_respondent_skill", "Skill Bridge Table", "bridge_respondent_skill.csv")


@st.cache_data(ttl=3600)
def load_skill_rules() -> pd.DataFrame:
    return _safe_query("SELECT * FROM skill_association_rules", "Skill Association Rules", "skill_association_rules.csv")


@st.cache_data(ttl=3600)
def load_job_clusters() -> pd.DataFrame:
    return _safe_query("SELECT * FROM job_clusters", "Job Clusters", "job_clusters.csv")
