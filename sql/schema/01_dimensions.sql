-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- Schema: Dimension Tables
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- Design notes:
--   * All dimension keys are SERIAL surrogate keys, not natural keys.
--     Natural keys (country names, job titles) are messy across three
--     independently-collected sources -- surrogate keys insulate the
--     fact tables from that mess and make joins cheap integer joins.
--   * dim_date is deliberately YEAR-grain, not day-grain. All three
--     sources are annual snapshots/surveys, not transactional data with
--     real dates. A day-grain date dimension would be 365x too fine and
--     imply precision the data doesn't have.
--   * dim_role_family exists to reconcile three different role
--     taxonomies (jobs_fact's 10 data-specific categories, Levels.fyi's
--     8 broad tech titles, and Stack Overflow's DevType free-text/multi
--     select). See docs/business_glossary.md (Phase 9) for the mapping
--     rules once finalized in Phase 5 (EDA) / Phase 7 (feature engineering).
-- =====================================================================

CREATE TABLE dim_date (
    date_key            SMALLINT PRIMARY KEY,       -- e.g. 2024 (year as key, since grain = year)
    work_year            SMALLINT NOT NULL UNIQUE,
    decade               VARCHAR(10) NOT NULL,        -- '2020s'
    is_current_year       BOOLEAN NOT NULL DEFAULT FALSE
);
COMMENT ON TABLE dim_date IS 'Year-grain date dimension. All sources are annual snapshots, not daily transactions.';

CREATE TABLE dim_country (
    country_key          SERIAL PRIMARY KEY,
    country_name          VARCHAR(100) NOT NULL UNIQUE,
    iso_alpha2            CHAR(2),
    region                 VARCHAR(50),                -- enrichment target for World Bank/OECD join (Phase 4.1 optional)
    continent              VARCHAR(50)
);
COMMENT ON TABLE dim_country IS 'Conformed country dimension shared by all three fact tables.';

CREATE TABLE dim_experience_level (
    experience_level_key   SERIAL PRIMARY KEY,
    level_name              VARCHAR(30) NOT NULL UNIQUE,   -- 'Entry-level','Mid-level','Senior','Executive'
    sort_order              SMALLINT NOT NULL              -- for correct chart/DAX ordering, not alphabetical
);
COMMENT ON TABLE dim_experience_level IS 'Ordered categorical -- sort_order drives Power BI axis ordering.';

CREATE TABLE dim_employment_type (
    employment_type_key    SERIAL PRIMARY KEY,
    type_name               VARCHAR(30) NOT NULL UNIQUE    -- 'Full-time','Part-time','Contract','Freelance'
);

CREATE TABLE dim_company_size (
    company_size_key       SERIAL PRIMARY KEY,
    size_code               CHAR(1) NOT NULL UNIQUE,        -- 'S','M','L'
    size_label               VARCHAR(20) NOT NULL,
    sort_order               SMALLINT NOT NULL
);

CREATE TABLE dim_remote_status (
    remote_status_key      SERIAL PRIMARY KEY,
    status_name              VARCHAR(20) NOT NULL UNIQUE     -- 'Remote','Hybrid','In-person'
);

CREATE TABLE dim_education_level (
    education_key           SERIAL PRIMARY KEY,
    education_name            VARCHAR(50) NOT NULL UNIQUE,   -- 'PhD','Master''s Degree','Bachelor''s Degree', ...
    sort_order                 SMALLINT NOT NULL
);

CREATE TABLE dim_role_family (
    role_family_key           SERIAL PRIMARY KEY,
    role_family_name            VARCHAR(100) NOT NULL UNIQUE, -- conformed label, e.g. 'Data Science & Research'
    role_category                VARCHAR(50) NOT NULL         -- coarser grouping, e.g. 'Data & Analytics' vs 'Software Engineering'
);
COMMENT ON TABLE dim_role_family IS 'Conformed role taxonomy reconciling job_category (jobs_fact), title (Levels.fyi), and DevType (Stack Overflow).';

CREATE TABLE dim_company (
    company_key                SERIAL PRIMARY KEY,
    company_name                  VARCHAR(200) NOT NULL UNIQUE
);
COMMENT ON TABLE dim_company IS 'Populated from Levels.fyi only -- the other two sources do not name employers.';

CREATE TABLE dim_skill (
    skill_key                    SERIAL PRIMARY KEY,
    skill_name                     VARCHAR(100) NOT NULL,
    skill_category                  VARCHAR(30) NOT NULL,      -- 'Language','Database','Platform','Webframe','Tool'
    UNIQUE (skill_name, skill_category)
);
COMMENT ON TABLE dim_skill IS 'Populated by unpivoting Stack Overflow''s semicolon-delimited *HaveWorkedWith columns (Phase 6, NLP module).';
