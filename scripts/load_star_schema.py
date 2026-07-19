"""
Loads the cleaned CSVs in data/processed/ into the normalized PostgreSQL
star schema defined in sql/schema/01_dimensions.sql, 02_facts.sql,
03_bridge_tables.sql, and 04_indexes.sql.
Author: Md Imamuddin

This replaces the old scripts/load_to_postgres.py, which loaded flat
tables (df.to_sql(..., if_exists="replace")) that didn't match this
schema at all -- no surrogate keys, no foreign keys, dropping and
recreating tables on every run. That script is removed. This is the
only loader now, and it is meant to be re-run safely: dimensions are
inserted with ON CONFLICT DO NOTHING (never duplicated), and fact /
bridge tables are truncated and reloaded, but never dropped, so the
schema, constraints, and indexes from sql/schema/ always stay intact.

Where the harder mapping logic comes from:
Two small reference files do the actual reconciliation work that
dim_country and dim_role_family need -- raw country spelling ->
canonical country (data/processed/dim_country_resolution.csv), and
job_category / title / DevType -> a conformed role family
(data/processed/dim_role_family_mapping.csv). Both were originally
built and checked in notebooks/09_sql_analytics_layer.ipynb against a
throwaway SQLite copy of this same schema (see
notebooks/reports/job_market_warehouse.db). This script reproduces
that same logic against real PostgreSQL -- it isn't a new set of
business rules invented for this script, it's the notebook's own
reconciliation work, promoted out of a notebook cell into something
repeatable. The role-family mapping is a first pass, not an
exhaustive taxonomy -- see docs/business_glossary.md's note on
dim_role_family for what's still open.

Usage:
    1. Create a PostgreSQL database and apply the schema (this script
       does NOT create tables):
         psql "$DATABASE_URL" -f sql/schema/01_dimensions.sql
         psql "$DATABASE_URL" -f sql/schema/02_facts.sql
         psql "$DATABASE_URL" -f sql/schema/03_bridge_tables.sql
         psql "$DATABASE_URL" -f sql/schema/04_indexes.sql
    2. export DATABASE_URL="postgresql://user:pass@localhost:5432/job_market_db"
    3. pip install -r streamlit_app/requirements-database.txt
    4. python scripts/load_star_schema.py

Safe to re-run: dimension rows are never duplicated, and fact/bridge
tables are truncated and reloaded fresh each time rather than appended
to, so running this twice in a row gives you the same row counts, not
double the rows.
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT / "src"))
from utils.logger import get_logger  # noqa: E402

logger = get_logger("load_star_schema")

DATA_DIR = REPO_ROOT / "data" / "processed"

REQUIRED_FILES = [
    "jobs_fact_clean.csv",
    "levels_fyi_clean.csv",
    "so_salary_clean.csv",
    "so_skills_clean.csv",
    "dim_skill.csv",
    "bridge_respondent_skill.csv",
    "dim_country_resolution.csv",
    "dim_role_family_mapping.csv",
]


def validate_inputs():
    """Check every CSV this script needs exists before touching the database.
    Failing here with a clear message is much friendlier than failing
    halfway through a load with half the tables populated."""
    missing = [f for f in REQUIRED_FILES if not (DATA_DIR / f).exists()]
    if missing:
        logger.error("Missing required input file(s):")
        for f in missing:
            logger.error(f"  - {DATA_DIR / f}")
        raise SystemExit(
            "Cannot proceed -- one or more processed CSVs are missing.\n"
            "Run the ETL scripts in src/etl/ first (see README.md's "
            "'Reproducing the ETL pipeline' section), or confirm you're "
            "running this from a checkout that already includes data/processed/."
        )
    logger.info(f"All {len(REQUIRED_FILES)} required input files found in {DATA_DIR}")


def get_engine():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is not set.\n"
            "Set it before running this script, for example:\n"
            '  export DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/job_market_db"\n'
            "Replace USER/PASSWORD with your own local PostgreSQL credentials."
        )
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise SystemExit(
            f"Could not connect to the database at the given DATABASE_URL.\n"
            f"Underlying error: {exc}\n"
            "Check that PostgreSQL is running and the schema has already "
            "been created (see this file's docstring, step 1)."
        )
    logger.info("Connected to PostgreSQL")
    return engine


# ---------------------------------------------------------------------
# Dimension loading
# ---------------------------------------------------------------------
# Every dimension is loaded the same way: build the dataframe of rows
# that *should* exist, push it into a staging table, then
# INSERT ... SELECT ... ON CONFLICT (unique_cols) DO NOTHING into the
# real table. That means re-running this script never creates a
# duplicate dimension member -- the unique constraints already defined
# in sql/schema/01_dimensions.sql are what actually enforce this, this
# function just avoids throwing an error when a conflict happens.

def upsert_dimension(engine, table_name: str, unique_cols: list, df: pd.DataFrame) -> tuple:
    if df.empty:
        logger.warning(f"{table_name}: nothing to load, dataframe is empty")
        return 0, 0

    staging_table = f"_staging_{table_name}"
    cols = ", ".join(df.columns)
    conflict_cols = ", ".join(unique_cols)

    with engine.begin() as conn:
        before = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        df.to_sql(staging_table, conn, if_exists="replace", index=False)
        conn.execute(text(
            f"INSERT INTO {table_name} ({cols}) "
            f"SELECT {cols} FROM {staging_table} "
            f"ON CONFLICT ({conflict_cols}) DO NOTHING"
        ))
        conn.execute(text(f"DROP TABLE {staging_table}"))
        after = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    inserted = after - before
    skipped = len(df) - inserted
    logger.info(f"{table_name}: inserted {inserted} new row(s), skipped {skipped} already present")
    return inserted, skipped


def load_dim_date(engine, jobs_df, levels_df, so_work_years: set) -> dict:
    levels_years = pd.to_datetime(levels_df["timestamp"]).dt.year
    years = set(jobs_df["work_year"].unique()) | set(levels_years.unique()) | so_work_years

    rows = []
    for year in sorted(years):
        year = int(year)
        rows.append({
            "date_key": year,
            "work_year": year,
            "decade": f"{(year // 10) * 10}s",
            "is_current_year": year == 2024,
        })
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_date", ["date_key"], df)

    with engine.connect() as conn:
        existing = pd.read_sql("SELECT date_key, work_year FROM dim_date", conn)
    return dict(zip(existing["work_year"], existing["date_key"]))


def load_dim_country(engine) -> dict:
    resolution = pd.read_csv(DATA_DIR / "dim_country_resolution.csv")

    dim_df = (
        resolution[["canonical_name", "iso_alpha2", "continent"]]
        .drop_duplicates(subset="canonical_name")
        .rename(columns={"canonical_name": "country_name"})
        .sort_values("country_name")
        .reset_index(drop=True)
    )
    # region is a deliberately-unpopulated enrichment column (World Bank/OECD
    # join, marked optional in sql/schema/01_dimensions.sql) -- not something
    # this ETL is skipping by mistake.
    dim_df["region"] = None
    dim_df = dim_df[["country_name", "iso_alpha2", "region", "continent"]]

    upsert_dimension(engine, "dim_country", ["country_name"], dim_df)

    with engine.connect() as conn:
        keys = pd.read_sql("SELECT country_key, country_name FROM dim_country", conn)
    canonical_to_key = dict(zip(keys["country_name"], keys["country_key"]))

    # The lookup callers actually need is keyed by the RAW string as it
    # appears in each of the three source files (e.g. "Korea, South" or
    # "United States of America"), not the canonical name.
    raw_to_canonical = dict(zip(resolution["raw_country_string"], resolution["canonical_name"]))
    raw_to_key = {
        raw: canonical_to_key[canonical]
        for raw, canonical in raw_to_canonical.items()
        if canonical in canonical_to_key
    }
    unresolved = set(raw_to_canonical) - set(raw_to_key)
    if unresolved:
        logger.warning(f"dim_country: {len(unresolved)} raw country string(s) had no matching dim row: {unresolved}")
    return raw_to_key


def load_dim_experience_level(engine) -> dict:
    # Fixed, small, ordered set -- matches jobs_fact_clean.csv's
    # experience_level values exactly (verified against the data before
    # writing this script).
    rows = [
        {"level_name": "Entry-level", "sort_order": 1},
        {"level_name": "Mid-level", "sort_order": 2},
        {"level_name": "Senior", "sort_order": 3},
        {"level_name": "Executive", "sort_order": 4},
    ]
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_experience_level", ["level_name"], df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT experience_level_key, level_name FROM dim_experience_level", conn)
    return dict(zip(keys["level_name"], keys["experience_level_key"]))


def load_dim_employment_type(engine) -> dict:
    # Matches jobs_fact_clean.csv's employment_type values exactly.
    rows = [{"type_name": name} for name in ["Contract", "Freelance", "Full-time", "Part-time"]]
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_employment_type", ["type_name"], df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT employment_type_key, type_name FROM dim_employment_type", conn)
    return dict(zip(keys["type_name"], keys["employment_type_key"]))


def load_dim_company_size(engine) -> dict:
    rows = [
        {"size_code": "S", "size_label": "Small", "sort_order": 1},
        {"size_code": "M", "size_label": "Medium", "sort_order": 2},
        {"size_code": "L", "size_label": "Large", "sort_order": 3},
    ]
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_company_size", ["size_code"], df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT company_size_key, size_code FROM dim_company_size", conn)
    return dict(zip(keys["size_code"], keys["company_size_key"]))


def load_dim_remote_status(engine) -> dict:
    # Matches jobs_fact_clean.csv's work_setting values exactly.
    rows = [{"status_name": name} for name in ["Hybrid", "In-person", "Remote"]]
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_remote_status", ["status_name"], df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT remote_status_key, status_name FROM dim_remote_status", conn)
    return dict(zip(keys["status_name"], keys["remote_status_key"]))


def load_dim_education_level(engine) -> dict:
    """
    Both source surveys ask about education, but with different wording
    and different granularity (Levels.fyi has 5 raw values, the Stack
    Overflow survey has 8). This conforms both to one 6-value scale.
    Anything not covered by either raw vocabulary (there isn't anything,
    but this is deliberately a dict.get(..., None) below, not a KeyError)
    ends up NULL, which the schema allows for both fact tables that use it.
    """
    rows = [
        {"education_name": "Primary/Secondary Education", "sort_order": 1},
        {"education_name": "Some College / Associate Degree", "sort_order": 2},
        {"education_name": "Bachelor's Degree", "sort_order": 3},
        {"education_name": "Master's Degree", "sort_order": 4},
        {"education_name": "Professional / Doctorate Degree", "sort_order": 5},
        {"education_name": "Other / Not Specified", "sort_order": 6},
    ]
    df = pd.DataFrame(rows)
    upsert_dimension(engine, "dim_education_level", ["education_name"], df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT education_key, education_name FROM dim_education_level", conn)
    name_to_key = dict(zip(keys["education_name"], keys["education_key"]))

    levels_fyi_raw_to_name = {
        "Highschool": "Primary/Secondary Education",
        "Some College": "Some College / Associate Degree",
        "Bachelor's Degree": "Bachelor's Degree",
        "Master's Degree": "Master's Degree",
        "PhD": "Professional / Doctorate Degree",
    }
    so_raw_to_name = {
        "Primary/elementary school": "Primary/Secondary Education",
        "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)": "Primary/Secondary Education",
        "Associate degree (A.A., A.S., etc.)": "Some College / Associate Degree",
        "Some college/university study without earning a degree": "Some College / Associate Degree",
        "Bachelor\u2019s degree (B.A., B.S., B.Eng., etc.)": "Bachelor's Degree",
        "Master\u2019s degree (M.A., M.S., M.Eng., MBA, etc.)": "Master's Degree",
        "Professional degree (JD, MD, Ph.D, Ed.D, etc.)": "Professional / Doctorate Degree",
        "Something else": "Other / Not Specified",
    }
    levels_fyi_lookup = {raw: name_to_key[name] for raw, name in levels_fyi_raw_to_name.items()}
    so_lookup = {raw: name_to_key[name] for raw, name in so_raw_to_name.items()}
    return levels_fyi_lookup, so_lookup


def load_dim_role_family(engine) -> dict:
    mapping = pd.read_csv(DATA_DIR / "dim_role_family_mapping.csv")

    dim_df = (
        mapping[["role_family_name", "role_category"]]
        .drop_duplicates(subset="role_family_name")
        .sort_values("role_family_name")
        .reset_index(drop=True)
    )
    upsert_dimension(engine, "dim_role_family", ["role_family_name"], dim_df)

    with engine.connect() as conn:
        keys = pd.read_sql("SELECT role_family_key, role_family_name FROM dim_role_family", conn)
    name_to_key = dict(zip(keys["role_family_name"], keys["role_family_key"]))

    # lookup is keyed by (source, raw_value), matching the 3 distinct
    # "source" labels used in dim_role_family_mapping.csv
    raw_to_key = {
        (row.source, row.raw_value): name_to_key[row.role_family_name]
        for row in mapping.itertuples()
        if row.role_family_name in name_to_key
    }
    return raw_to_key


def load_dim_company(engine, levels_df) -> dict:
    # First-appearance order, not alphabetical -- there's no natural
    # ordering for company names the way there is for, say, experience
    # levels, so insertion order is as good a default as any and it's
    # simple to reason about.
    companies = levels_df["company"].dropna().drop_duplicates().tolist()
    dim_df = pd.DataFrame({"company_name": companies})
    # 5 rows in levels_fyi_clean.csv have no company name at all. Rather
    # than drop those rows from the fact table (losing real compensation
    # data points over one missing field) or leaving a NOT NULL FK
    # unsatisfied, they get an explicit "Unknown" sentinel row -- visible
    # in any query, not silently blank.
    dim_df = pd.concat([dim_df, pd.DataFrame({"company_name": ["Unknown"]})], ignore_index=True)

    upsert_dimension(engine, "dim_company", ["company_name"], dim_df)
    with engine.connect() as conn:
        keys = pd.read_sql("SELECT company_key, company_name FROM dim_company", conn)
    return dict(zip(keys["company_name"], keys["company_key"]))


def load_dim_skill(engine):
    """
    dim_skill.csv already has skill_key values assigned by
    src/etl/build_skill_bridge.py, and bridge_respondent_skill.csv
    already references those exact keys. So unlike every other
    dimension in this script, this one preserves the CSV's keys as-is
    instead of letting PostgreSQL assign fresh SERIAL values -- if it
    didn't, the bridge table load later in this script would be
    pointing at the wrong skills.
    """
    df = pd.read_csv(DATA_DIR / "dim_skill.csv")
    staging_table = "_staging_dim_skill"
    with engine.begin() as conn:
        before = conn.execute(text("SELECT COUNT(*) FROM dim_skill")).scalar()
        df.to_sql(staging_table, conn, if_exists="replace", index=False)
        conn.execute(text(
            "INSERT INTO dim_skill (skill_key, skill_name, skill_category) "
            "SELECT skill_key, skill_name, skill_category FROM _staging_dim_skill "
            "ON CONFLICT (skill_name, skill_category) DO NOTHING"
        ))
        conn.execute(text(f"DROP TABLE {staging_table}"))
        after = conn.execute(text("SELECT COUNT(*) FROM dim_skill")).scalar()
        # Explicit-key inserts don't advance dim_skill's SERIAL sequence,
        # so anything inserted through this table by any other means
        # later would start colliding with these keys. Resync it now.
        conn.execute(text(
            "SELECT setval(pg_get_serial_sequence('dim_skill', 'skill_key'), "
            "GREATEST((SELECT MAX(skill_key) FROM dim_skill), 1))"
        ))
    logger.info(f"dim_skill: inserted {after - before} new row(s), skipped {len(df) - (after - before)} already present")


# ---------------------------------------------------------------------
# Fact + bridge loading
# ---------------------------------------------------------------------

def clear_facts_and_bridge(engine):
    """
    Per the project's rule for this script: never DROP TABLE, never
    CREATE TABLE, the schema is already there. Facts and the bridge
    table get truncated and reloaded fresh on every run instead.

    All four have to be truncated in a single statement, not four
    separate ones -- PostgreSQL refuses to truncate fact_so_respondent
    on its own while bridge_respondent_skill still has a foreign key
    pointing at it, even within the same transaction. Confirmed against
    a real PostgreSQL instance while writing this script; the fix is
    one combined TRUNCATE rather than sequential calls.
    """
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE TABLE bridge_respondent_skill, fact_job_postings, "
            "fact_levels_compensation, fact_so_respondent"
        ))
    logger.info("Truncated fact_job_postings, fact_levels_compensation, fact_so_respondent, bridge_respondent_skill")


def lookup_or_skip(value, lookup: dict, row_id, column_name: str, skip_counter: dict):
    """For NOT NULL foreign keys: return the surrogate key, or None plus
    a log entry if the raw value has no match. A None here means the
    caller drops that row rather than inserting a value that would
    violate a NOT NULL or foreign key constraint."""
    key = lookup.get(value)
    if key is None:
        skip_counter[column_name] = skip_counter.get(column_name, 0) + 1
        if skip_counter[column_name] <= 5:  # don't flood the log past the first few
            logger.warning(f"No {column_name} match for value {value!r} (row id {row_id}) -- row will be skipped")
    return key


def parse_so_employment_type(raw_value, employment_lookup: dict):
    """
    The Stack Overflow survey's Employment field is a semicolon-delimited
    multi-select (e.g. "Employed, full-time;Student, part-time"), unlike
    every other source in this project. There's no single clean mapping
    for someone who is simultaneously employed full-time AND a student,
    so this applies a priority order -- checked against the reference
    warehouse in notebooks/reports/job_market_warehouse.db before writing
    this: full-time beats part-time beats freelance/contract, and
    anything that matches none of those (student-only, unemployed,
    retired, "prefer not to say", etc.) is left NULL, which the schema
    allows for this column.
    """
    if pd.isna(raw_value):
        return None
    if "Employed, full-time" in raw_value:
        return employment_lookup.get("Full-time")
    if "Employed, part-time" in raw_value:
        return employment_lookup.get("Part-time")
    if "Independent contractor, freelancer, or self-employed" in raw_value:
        return employment_lookup.get("Freelance")
    return None


def load_fact_job_postings(engine, jobs_df, lookups):
    country_lookup = lookups["country"]
    experience_lookup = lookups["experience"]
    employment_lookup = lookups["employment"]
    size_lookup = lookups["company_size"]
    remote_lookup = lookups["remote"]
    role_family_lookup = lookups["role_family"]
    date_lookup = lookups["date"]

    skip_counter = {}
    rows = []
    for row in jobs_df.itertuples():
        country_key = lookup_or_skip(row.company_location, country_lookup, row.job_id, "country_key", skip_counter)
        employee_country_key = lookup_or_skip(row.employee_residence, country_lookup, row.job_id, "employee_country_key", skip_counter)
        experience_level_key = lookup_or_skip(row.experience_level, experience_lookup, row.job_id, "experience_level_key", skip_counter)
        employment_type_key = lookup_or_skip(row.employment_type, employment_lookup, row.job_id, "employment_type_key", skip_counter)
        company_size_key = lookup_or_skip(row.company_size, size_lookup, row.job_id, "company_size_key", skip_counter)
        remote_status_key = lookup_or_skip(row.work_setting, remote_lookup, row.job_id, "remote_status_key", skip_counter)
        role_family_key = lookup_or_skip(
            ("jobs_in_data_2024 (job_category)", row.job_category), role_family_lookup, row.job_id, "role_family_key", skip_counter
        )
        date_key = date_lookup.get(row.work_year)

        # every one of these is a NOT NULL foreign key in fact_job_postings --
        # if any lookup failed, this row can't be inserted at all.
        if None in (country_key, employee_country_key, experience_level_key, employment_type_key,
                    company_size_key, remote_status_key, role_family_key, date_key):
            continue

        rows.append({
            "job_id": row.job_id,
            "date_key": date_key,
            "country_key": country_key,
            "employee_country_key": employee_country_key,
            "experience_level_key": experience_level_key,
            "employment_type_key": employment_type_key,
            "company_size_key": company_size_key,
            "role_family_key": role_family_key,
            "remote_status_key": remote_status_key,
            "job_title": row.job_title,
            "salary_usd": row.salary_in_usd,
            "salary_is_outlier": bool(row.salary_is_outlier),
            "source_dataset": row.source_dataset,
        })

    fact_df = pd.DataFrame(rows)
    skipped_total = len(jobs_df) - len(fact_df)
    with engine.begin() as conn:
        fact_df.to_sql("fact_job_postings", conn, if_exists="append", index=False)
    logger.info(f"fact_job_postings: loaded {len(fact_df)} rows, skipped {skipped_total} (lookup failures)")


def _sanitize_gender(raw_value, record_id):
    """
    One row in levels_fyi_clean.csv (record_id 11011) has "Title: Senior
    Software Engineer" sitting in the gender field -- clearly a
    data-collection artifact, not a real response, and it doesn't fit
    the schema's VARCHAR(20) (which is a reasonable limit for every
    genuine gender value in this dataset -- found by actually running
    this loader against PostgreSQL, not a hypothetical). Rather than
    truncate it into meaningless partial text or widen a column limit
    that's fine everywhere else, this stores NULL for that one row and
    logs it, leaving the row itself in the fact table.
    """
    if pd.isna(raw_value):
        return None
    if len(raw_value) > 20:
        logger.warning(f"record_id {record_id}: gender value {raw_value!r} exceeds 20 chars, storing NULL instead")
        return None
    return raw_value


def load_fact_levels_compensation(engine, levels_df, lookups):
    country_lookup = lookups["country"]
    role_family_lookup = lookups["role_family"]
    company_lookup = lookups["company"]
    levels_fyi_education_lookup = lookups["education_levels_fyi"]

    levels_df = levels_df.copy()
    levels_df["year"] = pd.to_datetime(levels_df["timestamp"]).dt.year

    skip_counter = {}
    rows = []
    for row in levels_df.itertuples():
        country_key = lookup_or_skip(row.country, country_lookup, row.record_id, "country_key", skip_counter)
        role_family_key = lookup_or_skip(
            ("levels_fyi (title)", row.title), role_family_lookup, row.record_id, "role_family_key", skip_counter
        )
        company_name = row.company if pd.notna(row.company) else "Unknown"
        company_key = lookup_or_skip(company_name, company_lookup, row.record_id, "company_key", skip_counter)
        date_key = int(row.year)

        # education_key is genuinely nullable in this fact table -- a
        # missing/unmapped value becomes NULL, not a skipped row.
        education_key = levels_fyi_education_lookup.get(row.Education) if pd.notna(row.Education) else None

        if None in (country_key, role_family_key, company_key):
            continue

        rows.append({
            "record_id": row.record_id,
            "date_key": date_key,
            "company_key": company_key,
            "country_key": country_key,
            "role_family_key": role_family_key,
            "education_key": education_key,
            "city": row.city if pd.notna(row.city) else None,
            "region": row.region if pd.notna(row.region) else None,
            "total_yearly_compensation": row.total_yearly_compensation,
            "base_salary": row.base_salary,
            "stock_grant_value": row.stock_grant_value,
            "bonus": row.bonus,
            "years_of_experience": row.years_of_experience,
            "years_at_company": row.years_at_company,
            "gender": _sanitize_gender(row.gender, row.record_id),
            "total_comp_is_outlier": bool(row.total_comp_is_outlier),
            "source_dataset": row.source_dataset,
        })

    fact_df = pd.DataFrame(rows)
    skipped_total = len(levels_df) - len(fact_df)
    with engine.begin() as conn:
        fact_df.to_sql("fact_levels_compensation", conn, if_exists="append", index=False)
    logger.info(f"fact_levels_compensation: loaded {len(fact_df)} rows, skipped {skipped_total} (lookup failures)")


def _parse_years_code_pro(raw_value):
    """
    YearsCodePro is mostly a plain number as a string, but the survey
    lets respondents answer "Less than 1 year" or "More than 50 years"
    instead of a number -- found by running this against PostgreSQL,
    which (correctly) rejects non-numeric text for a NUMERIC(4,1)
    column. Mapped to 0.5 and 50.0 respectively, the standard convention
    for this specific Stack Overflow survey field.
    """
    if pd.isna(raw_value):
        return None
    if raw_value == "Less than 1 year":
        return 0.5
    if raw_value == "More than 50 years":
        return 50.0
    return float(raw_value)


def load_fact_so_respondent(engine, so_skills_df, so_salary_df, lookups):
    country_lookup = lookups["country"]
    role_family_lookup = lookups["role_family"]
    education_lookup = lookups["education_so"]
    employment_lookup = lookups["employment"]

    # so_skills_clean.csv has all 65,437 respondents (this fact table's
    # documented grain); so_salary_clean.csv is the ~36% who reported
    # comp, plus the below_sanity_floor/comp_is_outlier flags computed
    # only for that subset. Confirmed against the data before writing
    # this: every ConvertedCompYearly value in so_skills_clean.csv
    # already matches so_salary_clean.csv for the respondents both
    # contain, so this is a left join adding two flag columns, not a
    # merge of two different compensation figures.
    flags = so_salary_df[["ResponseId", "below_sanity_floor", "comp_is_outlier"]]
    merged = so_skills_df.merge(flags, on="ResponseId", how="left")
    merged["below_sanity_floor"] = merged["below_sanity_floor"].fillna(False)
    merged["comp_is_outlier"] = merged["comp_is_outlier"].fillna(False)

    skip_counter = {}
    rows = []
    for row in merged.itertuples():
        country_key = country_lookup.get(row.Country) if pd.notna(row.Country) else None
        role_family_key = role_family_lookup.get(("stackoverflow_2024 (DevType)", row.DevType)) if pd.notna(row.DevType) else None
        education_key = education_lookup.get(row.EdLevel) if pd.notna(row.EdLevel) else None
        employment_type_key = parse_so_employment_type(row.Employment, employment_lookup)

        rows.append({
            "response_id": row.ResponseId,
            "date_key": 2024,  # the survey itself is a single-year snapshot
            "country_key": country_key,
            "role_family_key": role_family_key,
            "employment_type_key": employment_type_key,
            "education_key": education_key,
            "years_code_pro": _parse_years_code_pro(row.YearsCodePro),
            "org_size": row.OrgSize if pd.notna(row.OrgSize) else None,
            "industry": row.Industry if pd.notna(row.Industry) else None,
            "comp_usd": row.ConvertedCompYearly if pd.notna(row.ConvertedCompYearly) else None,
            "below_sanity_floor": bool(row.below_sanity_floor),
            "comp_is_outlier": bool(row.comp_is_outlier),
            "source_dataset": row.source_dataset,
        })

    fact_df = pd.DataFrame(rows)
    # every FK on this fact table is nullable, so nothing gets skipped here --
    # unlike the other two fact loaders, every source row becomes a fact row.
    with engine.begin() as conn:
        fact_df.to_sql("fact_so_respondent", conn, if_exists="append", index=False)
    logger.info(f"fact_so_respondent: loaded {len(fact_df)} rows (0 skipped -- every FK on this table is nullable)")


def load_bridge_respondent_skill(engine, bridge_df):
    # response_id and skill_key are both preserved as-is from the CSV --
    # they need to match rows already inserted into fact_so_respondent
    # and dim_skill. bridge_id itself is dropped and left for PostgreSQL
    # to assign fresh, since nothing else references it.
    df = bridge_df[["response_id", "skill_key"]]
    with engine.begin() as conn:
        df.to_sql("bridge_respondent_skill", conn, if_exists="append", index=False)
    logger.info(f"bridge_respondent_skill: loaded {len(df)} rows")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    start = time.time()
    validate_inputs()
    engine = get_engine()

    jobs_df = pd.read_csv(DATA_DIR / "jobs_fact_clean.csv")
    levels_df = pd.read_csv(DATA_DIR / "levels_fyi_clean.csv")
    so_salary_df = pd.read_csv(DATA_DIR / "so_salary_clean.csv")
    so_skills_df = pd.read_csv(DATA_DIR / "so_skills_clean.csv")
    bridge_df = pd.read_csv(DATA_DIR / "bridge_respondent_skill.csv")
    logger.info(
        f"Loaded source CSVs: jobs={len(jobs_df)}, levels_fyi={len(levels_df)}, "
        f"so_salary={len(so_salary_df)}, so_skills={len(so_skills_df)}, bridge={len(bridge_df)}"
    )

    logger.info("--- Populating dimensions ---")
    lookups = {}
    lookups["date"] = load_dim_date(engine, jobs_df, levels_df, so_work_years={2024})
    lookups["country"] = load_dim_country(engine)
    lookups["experience"] = load_dim_experience_level(engine)
    lookups["employment"] = load_dim_employment_type(engine)
    lookups["company_size"] = load_dim_company_size(engine)
    lookups["remote"] = load_dim_remote_status(engine)
    lookups["education_levels_fyi"], lookups["education_so"] = load_dim_education_level(engine)
    lookups["role_family"] = load_dim_role_family(engine)
    lookups["company"] = load_dim_company(engine, levels_df)
    load_dim_skill(engine)

    logger.info("--- Clearing fact and bridge tables before reload ---")
    clear_facts_and_bridge(engine)

    logger.info("--- Populating fact tables ---")
    load_fact_job_postings(engine, jobs_df, lookups)
    load_fact_levels_compensation(engine, levels_df, lookups)
    load_fact_so_respondent(engine, so_skills_df, so_salary_df, lookups)

    logger.info("--- Populating bridge table ---")
    load_bridge_respondent_skill(engine, bridge_df)

    elapsed = time.time() - start
    logger.info(f"Done in {elapsed:.1f}s. Star schema loaded -- see sql/analysis_queries/ "
                f"and sql/views/ to query it (those already target these exact table names).")


if __name__ == "__main__":
    main()
