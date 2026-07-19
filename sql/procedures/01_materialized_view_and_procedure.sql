-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- SQL Analytics Layer: Materialized View + Stored Procedure
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- This file was originally syntax-reviewed only, not executed against
-- a live PostgreSQL server (see git history / reports/sql_validation_notes.md
-- for that history). It has since actually been run against a real
-- PostgreSQL 16 instance, both to adapt it to the star schema
-- (fact_job_postings no longer has company_location/salary_in_usd
-- directly -- both come from a join now, same as the rest of the SQL
-- analytics layer) and to fix a real bug that live execution caught:
-- PostgreSQL has no ROUND(double precision, integer) overload, and
-- PERCENTILE_CONT always returns double precision, so every ROUND(...)
-- around one below needs an explicit ::numeric cast. That's not a
-- star-schema issue -- it would have failed the same way against the
-- old flat table too, if this file had ever actually been run before.
-- =====================================================================

-- -----------------------------------------------------------------------
-- Materialized view: expensive aggregate refreshed on a schedule, not on
-- every query. Country benchmarking involves a percentile calculation
-- over the full fact table -- worth materializing if this feeds a
-- frequently-refreshed Power BI dashboard page rather than recomputing
-- on every report interaction.
-- -----------------------------------------------------------------------
CREATE MATERIALIZED VIEW mv_country_salary_benchmarks AS
SELECT
    c.country_name AS company_location,
    COUNT(*) AS n,
    ROUND(AVG(f.salary_usd), 0) AS avg_salary,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.salary_usd) AS median_salary,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY f.salary_usd) AS p25_salary,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.salary_usd) AS p75_salary
FROM fact_job_postings f
JOIN dim_country c ON f.country_key = c.country_key
GROUP BY c.country_name
HAVING COUNT(*) >= 30
WITH DATA;

CREATE UNIQUE INDEX idx_mv_country_benchmarks ON mv_country_salary_benchmarks(company_location);

-- Refresh strategy: CONCURRENTLY avoids locking readers out during refresh
-- (requires the unique index above). In production this would be called
-- from a scheduled job (cron / Airflow) after each ETL run, not manually.
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_salary_benchmarks;


-- -----------------------------------------------------------------------
-- Stored procedure: parameterized salary benchmarking lookup.
-- Business use case: a "salary check" feature where a user submits their
-- job_category and experience_level and gets back where they'd rank.
--
-- p_job_category now expects a role_family_name value (e.g.
-- 'Data Engineering', 'Machine Learning & AI') -- see dim_role_family --
-- rather than jobs_in_data_2024's original 10-value job_category column,
-- which no longer exists as a standalone column on the fact table.
-- -----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_salary_benchmark(
    p_job_category VARCHAR,
    p_experience_level VARCHAR,
    p_candidate_salary NUMERIC
)
RETURNS TABLE (
    category_median NUMERIC,
    category_avg NUMERIC,
    n_comparable INTEGER,
    candidate_percentile NUMERIC,
    verdict TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH comparable AS (
        SELECT f.salary_usd AS salary_in_usd
        FROM fact_job_postings f
        JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
        JOIN dim_experience_level el ON f.experience_level_key = el.experience_level_key
        WHERE rf.role_family_name = p_job_category
          AND el.level_name = p_experience_level
    )
    SELECT
        -- PERCENTILE_CONT returns double precision; this column is typed
        -- NUMERIC above, so it needs the same ::numeric cast the rest of
        -- this file needed once actually run against PostgreSQL.
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_in_usd))::numeric,
        ROUND(AVG(salary_in_usd), 0),
        COUNT(*)::INTEGER,
        ROUND(
            (SELECT COUNT(*) FROM comparable WHERE salary_in_usd <= p_candidate_salary) * 100.0
            / NULLIF((SELECT COUNT(*) FROM comparable), 0)
        , 1),
        CASE
            WHEN (SELECT COUNT(*) FROM comparable) < 30 THEN 'Insufficient data for a reliable benchmark (n<30)'
            WHEN p_candidate_salary < PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_in_usd) THEN 'Below market -- consider negotiating'
            WHEN p_candidate_salary > PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_in_usd) THEN 'Above market -- strong offer'
            ELSE 'Within typical market range'
        END
    FROM comparable;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_salary_benchmark IS
'Given a candidate''s job_category (a role_family_name -- see dim_role_family), experience_level, and current/offered salary, returns how they compare to the market with an explicit data-sufficiency check (n<30 triggers a caveat rather than a false-confidence verdict).';

-- Example call:
-- SELECT * FROM get_salary_benchmark('Data Engineering', 'Senior', 150000);
