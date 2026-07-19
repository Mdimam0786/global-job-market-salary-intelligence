-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- SQL Analytics Layer: Business KPI Queries
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- fact_job_postings stores surrogate keys (role_family_key, country_key,
-- date_key, remote_status_key, experience_level_key), not the raw
-- category/country/year strings these KPIs report on -- that's the
-- whole point of a star schema, but it means every query here starts
-- from a small CTE that joins fact_job_postings back to its
-- dimensions and re-exposes those readable names. Everything after
-- that CTE is the same business logic as before this schema migration
-- (same window functions, same business questions) -- only the source
-- of job_category / work_year / company_location / work_setting /
-- experience_level changed, not what's computed from them.
--
-- One real semantic note from the migration: job_category used to be
-- jobs_in_data_2024's own 10-value taxonomy. It's now role_family_name,
-- the 34-value taxonomy conformed across all three data sources (see
-- dim_role_family / docs/business_glossary.md). Two of the original 10
-- categories ("Data Quality and Operations" and "Data Management and
-- Strategy") map onto role families already used by another category,
-- so grouping by job_category here can now produce slightly fewer than
-- 10 distinct groups for this source's data -- expected, not a bug.
-- =====================================================================

-- -----------------------------------------------------------------------
-- KPI 1: Salary rank within job category + percentile (window functions)
-- Business question: "How does this specific salary compare to peers in
-- the same job category?" -- the basis of a "you are here" benchmarking
-- feature for job seekers.
-- -----------------------------------------------------------------------
WITH fact_job_postings_enriched AS (
    SELECT
        f.job_id,
        f.job_title,
        rf.role_family_name AS job_category,
        f.salary_usd AS salary_in_usd
    FROM fact_job_postings f
    JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
)
SELECT
    job_id,
    job_title,
    job_category,
    salary_in_usd,
    RANK() OVER (PARTITION BY job_category ORDER BY salary_in_usd DESC) AS rank_in_category,
    -- PERCENT_RANK() always returns double precision -- same ROUND cast
    -- issue as the other KPIs, needs an explicit ::numeric cast.
    ROUND(
        (PERCENT_RANK() OVER (PARTITION BY job_category ORDER BY salary_in_usd) * 100)::numeric, 1
    ) AS percentile_in_category,
    ROUND(AVG(salary_in_usd) OVER (PARTITION BY job_category), 0) AS category_avg_salary,
    salary_in_usd - ROUND(AVG(salary_in_usd) OVER (PARTITION BY job_category), 0) AS diff_from_category_avg
FROM fact_job_postings_enriched
ORDER BY job_category, rank_in_category
LIMIT 100;


-- -----------------------------------------------------------------------
-- KPI 2: Year-over-year median salary growth by job category (window LAG)
-- Business question: "Which job categories are growing fastest in pay?"
-- -----------------------------------------------------------------------
WITH fact_job_postings_enriched AS (
    SELECT
        f.job_id,
        rf.role_family_name AS job_category,
        f.date_key AS work_year,
        f.salary_usd AS salary_in_usd
    FROM fact_job_postings f
    JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
),
yearly_medians AS (
    SELECT
        job_category,
        work_year,
        -- PERCENTILE_CONT is an ordered-set aggregate, not a window
        -- function -- PostgreSQL rejects OVER(...) on it outright
        -- (confirmed by actually running this query). GROUP BY already
        -- gives exactly one row per (job_category, work_year), so the
        -- ROW_NUMBER-based dedup this used to need isn't necessary either.
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_in_usd) AS median_salary
    FROM fact_job_postings_enriched
    GROUP BY job_category, work_year
)
SELECT
    job_category,
    work_year,
    median_salary,
    LAG(median_salary) OVER (PARTITION BY job_category ORDER BY work_year) AS prior_year_median,
    -- PERCENTILE_CONT always returns double precision even over a
    -- numeric column, and PostgreSQL has no ROUND(double precision, int)
    -- overload -- confirmed by actually running this query, not assumed.
    -- Explicit ::numeric cast is required.
    ROUND((
        (median_salary - LAG(median_salary) OVER (PARTITION BY job_category ORDER BY work_year))
        / NULLIF(LAG(median_salary) OVER (PARTITION BY job_category ORDER BY work_year), 0) * 100
    )::numeric, 1) AS yoy_growth_pct
FROM yearly_medians
ORDER BY job_category, work_year;


-- -----------------------------------------------------------------------
-- KPI 3: Top 3 highest-paying job titles per category (window + filter)
-- Business question: "Within each category, what should I aim for?"
-- -----------------------------------------------------------------------
WITH fact_job_postings_enriched AS (
    SELECT
        f.job_title,
        rf.role_family_name AS job_category,
        f.salary_usd AS salary_in_usd
    FROM fact_job_postings f
    JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
),
title_stats AS (
    SELECT
        job_category,
        job_title,
        COUNT(*) AS n,
        ROUND(AVG(salary_in_usd), 0) AS avg_salary
    FROM fact_job_postings_enriched
    GROUP BY job_category, job_title
    HAVING COUNT(*) >= 10   -- exclude titles too thin to trust
),
ranked_titles AS (
    SELECT
        *,
        DENSE_RANK() OVER (PARTITION BY job_category ORDER BY avg_salary DESC) AS rnk
    FROM title_stats
)
SELECT job_category, job_title, n, avg_salary, rnk
FROM ranked_titles
WHERE rnk <= 3
ORDER BY job_category, rnk;


-- -----------------------------------------------------------------------
-- KPI 4: Remote work adoption trend + salary impact, by year (CTE + window)
-- Business question: "Is the return-to-office trend costing or saving
-- companies money, and how has adoption shifted?"
-- -----------------------------------------------------------------------
WITH fact_job_postings_enriched AS (
    SELECT
        f.date_key AS work_year,
        rs.status_name AS work_setting,
        f.salary_usd AS salary_in_usd
    FROM fact_job_postings f
    JOIN dim_remote_status rs ON f.remote_status_key = rs.remote_status_key
),
yearly_remote AS (
    SELECT
        work_year,
        work_setting,
        COUNT(*) AS n,
        ROUND(AVG(salary_in_usd), 0) AS avg_salary
    FROM fact_job_postings_enriched
    GROUP BY work_year, work_setting
),
yearly_totals AS (
    SELECT work_year, SUM(n) AS total_n
    FROM yearly_remote
    GROUP BY work_year
)
SELECT
    yr.work_year,
    yr.work_setting,
    yr.n,
    ROUND(yr.n * 100.0 / yt.total_n, 1) AS pct_of_postings,
    yr.avg_salary
FROM yearly_remote yr
JOIN yearly_totals yt ON yr.work_year = yt.work_year
ORDER BY yr.work_year, pct_of_postings DESC;


-- -----------------------------------------------------------------------
-- KPI 5: Country salary benchmarking with running rank (window function)
-- Business question: "Rank countries by median salary, restricted to
-- countries with enough data to be statistically meaningful."
-- -----------------------------------------------------------------------
WITH fact_job_postings_enriched AS (
    SELECT
        c.country_name AS company_location,
        f.salary_usd AS salary_in_usd
    FROM fact_job_postings f
    JOIN dim_country c ON f.country_key = c.country_key
),
country_stats AS (
    SELECT
        company_location,
        COUNT(*) AS n,
        ROUND(AVG(salary_in_usd), 0) AS avg_salary,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_in_usd) AS median_salary
    FROM fact_job_postings_enriched
    GROUP BY company_location
    HAVING COUNT(*) >= 30
)
SELECT
    company_location,
    n,
    avg_salary,
    median_salary,
    RANK() OVER (ORDER BY median_salary DESC) AS salary_rank,
    -- Same double-precision/ROUND issue as KPI 2 -- explicit cast needed.
    ROUND((median_salary / FIRST_VALUE(median_salary) OVER (ORDER BY median_salary DESC) * 100)::numeric, 1) AS pct_of_top_country
FROM country_stats
ORDER BY salary_rank;
