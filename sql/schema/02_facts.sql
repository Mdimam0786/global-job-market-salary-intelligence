-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- Schema: Fact Tables
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- Design notes:
--   * THREE fact tables, not one. Per the Phase 3 data quality report,
--     jobs_fact / levels_fyi / stack_overflow are different populations
--     with different collection methods -- unioning them into a single
--     "salary fact" would silently average three different labor
--     markets together. They share conformed dimensions instead, so
--     Power BI can slice each independently or compare side-by-side
--     without ever blending incompatible rows.
--   * Every outlier flag computed in Phase 3 (IQR-based) is carried
--     through as a boolean column, not resolved here. Filtering is a
--     reporting-layer decision, not an ETL decision -- baking it into
--     the warehouse would silently change what "salary" means for every
--     future consumer of the table.
--   * source_dataset is kept on every fact row for full provenance,
--     even though it's implied by which fact table you're querying --
--     useful once/if these are ever unioned into a semantic view.
-- =====================================================================

CREATE TABLE fact_job_postings (
    job_id                    INTEGER PRIMARY KEY,              -- surrogate key from Phase 3 ETL
    date_key                   SMALLINT NOT NULL REFERENCES dim_date(date_key),
    country_key                 INTEGER NOT NULL REFERENCES dim_country(country_key),      -- company_location
    employee_country_key          INTEGER NOT NULL REFERENCES dim_country(country_key),    -- employee_residence
    experience_level_key           INTEGER NOT NULL REFERENCES dim_experience_level(experience_level_key),
    employment_type_key             INTEGER NOT NULL REFERENCES dim_employment_type(employment_type_key),
    company_size_key                 INTEGER NOT NULL REFERENCES dim_company_size(company_size_key),
    role_family_key                    INTEGER NOT NULL REFERENCES dim_role_family(role_family_key),
    remote_status_key                    INTEGER NOT NULL REFERENCES dim_remote_status(remote_status_key),
    job_title                              VARCHAR(150) NOT NULL,      -- kept verbatim alongside the conformed role_family
    salary_usd                              NUMERIC(12,2) NOT NULL,
    salary_is_outlier                        BOOLEAN NOT NULL DEFAULT FALSE,
    source_dataset                             VARCHAR(50) NOT NULL DEFAULT 'jobs_in_data_2024'
);
COMMENT ON TABLE fact_job_postings IS 'Primary fact table. Grain: one row per survey respondent/posting record from jobs_in_data_2024.';

CREATE TABLE fact_levels_compensation (
    record_id                   INTEGER PRIMARY KEY,
    date_key                     SMALLINT NOT NULL REFERENCES dim_date(date_key),
    company_key                   INTEGER NOT NULL REFERENCES dim_company(company_key),
    country_key                     INTEGER NOT NULL REFERENCES dim_country(country_key),
    role_family_key                   INTEGER NOT NULL REFERENCES dim_role_family(role_family_key),
    education_key                       INTEGER REFERENCES dim_education_level(education_key),  -- nullable: 51.5% missing (Phase 3 finding)
    city                                   VARCHAR(100),
    region                                   VARCHAR(50),
    total_yearly_compensation                 NUMERIC(12,2) NOT NULL,
    base_salary                                 NUMERIC(12,2) NOT NULL,
    stock_grant_value                             NUMERIC(12,2) NOT NULL,
    bonus                                           NUMERIC(12,2) NOT NULL,
    years_of_experience                               NUMERIC(4,1) NOT NULL,
    years_at_company                                   NUMERIC(4,1) NOT NULL,
    gender                                               VARCHAR(20),              -- nullable: 31.2% missing, optional field
    total_comp_is_outlier                                 BOOLEAN NOT NULL DEFAULT FALSE,
    source_dataset                                          VARCHAR(50) NOT NULL DEFAULT 'levels_fyi'
);
COMMENT ON TABLE fact_levels_compensation IS 'Company/level compensation benchmarking. Grain: one row per Levels.fyi self-report. Big Tech-heavy population -- do not blend medians with fact_job_postings.';

CREATE TABLE fact_so_respondent (
    response_id                  INTEGER PRIMARY KEY,             -- ResponseId from the SO survey
    date_key                      SMALLINT NOT NULL REFERENCES dim_date(date_key),
    country_key                     INTEGER REFERENCES dim_country(country_key),        -- nullable: Country has nulls in source
    role_family_key                   INTEGER REFERENCES dim_role_family(role_family_key), -- nullable: DevType is multi-select/optional
    employment_type_key                 INTEGER REFERENCES dim_employment_type(employment_type_key),
    education_key                         INTEGER REFERENCES dim_education_level(education_key),
    years_code_pro                          NUMERIC(4,1),
    org_size                                  VARCHAR(50),
    industry                                    VARCHAR(100),
    comp_usd                                      NUMERIC(12,2),        -- NULL for the ~64% of respondents who skipped this field
    below_sanity_floor                              BOOLEAN NOT NULL DEFAULT FALSE,
    comp_is_outlier                                   BOOLEAN NOT NULL DEFAULT FALSE,
    source_dataset                                      VARCHAR(50) NOT NULL DEFAULT 'stackoverflow_2024'
);
COMMENT ON TABLE fact_so_respondent IS 'Grain: one row per SO survey respondent (all 65,437). comp_usd is NULL for respondents who did not report compensation -- filter WHERE comp_usd IS NOT NULL for salary analysis (equivalent to the so_salary_clean.csv view from Phase 3).';
