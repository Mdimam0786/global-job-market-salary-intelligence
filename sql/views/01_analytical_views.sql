-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- SQL Analytics Layer: Views
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- Views encapsulate the CTEs from 01_business_kpis.sql into reusable,
-- named objects that Power BI (or any BI tool) can query directly like
-- a table, instead of re-pasting a CTE into every report page.
--
-- Like 01_business_kpis.sql, every view here joins fact_job_postings
-- back to its dimension tables to recover the readable names
-- (job_category, company_location, work_setting, experience_level)
-- that used to live directly on the fact table before the star-schema
-- migration -- see that file's header comment for the one semantic
-- note on job_category now meaning role_family_name.
-- =====================================================================

CREATE OR REPLACE VIEW vw_salary_benchmarking AS
SELECT
    f.job_id,
    f.job_title,
    rf.role_family_name AS job_category,
    el.level_name AS experience_level,
    c.country_name AS company_location,
    f.salary_usd AS salary_in_usd,
    RANK() OVER (PARTITION BY rf.role_family_name ORDER BY f.salary_usd DESC) AS rank_in_category,
    ROUND(
        (PERCENT_RANK() OVER (PARTITION BY rf.role_family_name ORDER BY f.salary_usd) * 100)::numeric, 1
    ) AS percentile_in_category,
    ROUND(AVG(f.salary_usd) OVER (PARTITION BY rf.role_family_name), 0) AS category_avg_salary
FROM fact_job_postings f
JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
JOIN dim_experience_level el ON f.experience_level_key = el.experience_level_key
JOIN dim_country c ON f.country_key = c.country_key;

COMMENT ON VIEW vw_salary_benchmarking IS
'Per-row salary benchmarking against job category peers. Powers the "how do I compare" Power BI card in the Salary Intelligence dashboard.';


CREATE OR REPLACE VIEW vw_category_yearly_trends AS
SELECT
    rf.role_family_name AS job_category,
    f.date_key AS work_year,
    COUNT(*) AS n_postings,
    ROUND(AVG(f.salary_usd), 0) AS avg_salary,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.salary_usd) AS median_salary
FROM fact_job_postings f
JOIN dim_role_family rf ON f.role_family_key = rf.role_family_key
GROUP BY rf.role_family_name, f.date_key;

COMMENT ON VIEW vw_category_yearly_trends IS
'One row per (job_category, work_year). Base view for YoY growth DAX measures in Power BI -- Power BI''s time intelligence functions handle the LAG/growth-rate calculation natively once this view is the source table, so that logic is intentionally NOT duplicated in SQL here.';


CREATE OR REPLACE VIEW vw_country_benchmarks AS
SELECT
    c.country_name AS company_location,
    COUNT(*) AS n,
    ROUND(AVG(f.salary_usd), 0) AS avg_salary,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.salary_usd) AS median_salary,
    RANK() OVER (ORDER BY PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.salary_usd) DESC) AS salary_rank
FROM fact_job_postings f
JOIN dim_country c ON f.country_key = c.country_key
GROUP BY c.country_name
HAVING COUNT(*) >= 30;

COMMENT ON VIEW vw_country_benchmarks IS
'Country-level salary benchmarks, restricted to countries with >=30 respondents for statistical stability (see Phase 5 EDA caveats on thin-sample countries).';


CREATE OR REPLACE VIEW vw_remote_work_trend AS
SELECT
    f.date_key AS work_year,
    rs.status_name AS work_setting,
    COUNT(*) AS n,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY f.date_key), 1) AS pct_of_postings,
    ROUND(AVG(f.salary_usd), 0) AS avg_salary
FROM fact_job_postings f
JOIN dim_remote_status rs ON f.remote_status_key = rs.remote_status_key
GROUP BY f.date_key, rs.status_name;

COMMENT ON VIEW vw_remote_work_trend IS
'Remote/hybrid/in-person share and average pay by year. Powers the Remote Work Analysis dashboard page -- this is the query behind the 54%->24% remote-share finding from Phase 5 EDA.';


CREATE OR REPLACE VIEW vw_skill_demand AS
SELECT
    s.skill_name,
    s.skill_category,
    COUNT(DISTINCT b.response_id) AS respondent_count,
    ROUND(COUNT(DISTINCT b.response_id) * 100.0 /
        (SELECT COUNT(DISTINCT response_id) FROM bridge_respondent_skill), 2) AS pct_of_respondents
FROM dim_skill s
JOIN bridge_respondent_skill b ON s.skill_key = b.skill_key
GROUP BY s.skill_name, s.skill_category;

COMMENT ON VIEW vw_skill_demand IS
'Skill popularity ranking, powers the Skill Intelligence dashboard page and the word-cloud visual.';
