-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- Schema: Indexes
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- Foreign keys are NOT automatically indexed in PostgreSQL (unlike some
-- other RDBMS). Every FK used in a JOIN or WHERE filter in the planned
-- SQL analytics layer (Phase 5) gets an index here. Skipping this would
-- mean every dashboard filter triggers a sequential scan on tables with
-- tens of thousands of rows -- fine in a demo, embarrassing in a
-- "production-grade" portfolio claim.
-- =====================================================================

-- fact_job_postings
CREATE INDEX idx_fjp_country       ON fact_job_postings(country_key);
CREATE INDEX idx_fjp_exp_level     ON fact_job_postings(experience_level_key);
CREATE INDEX idx_fjp_role_family   ON fact_job_postings(role_family_key);
CREATE INDEX idx_fjp_date          ON fact_job_postings(date_key);
CREATE INDEX idx_fjp_remote        ON fact_job_postings(remote_status_key);

-- fact_levels_compensation
CREATE INDEX idx_flc_company       ON fact_levels_compensation(company_key);
CREATE INDEX idx_flc_country       ON fact_levels_compensation(country_key);
CREATE INDEX idx_flc_role_family   ON fact_levels_compensation(role_family_key);
CREATE INDEX idx_flc_date          ON fact_levels_compensation(date_key);

-- fact_so_respondent
CREATE INDEX idx_fsr_country       ON fact_so_respondent(country_key);
CREATE INDEX idx_fsr_role_family   ON fact_so_respondent(role_family_key);
CREATE INDEX idx_fsr_date          ON fact_so_respondent(date_key);
-- Partial index: most analytical queries on this table filter to
-- respondents who actually reported compensation (~36% of rows) --
-- a partial index keeps it small and fast instead of indexing all 65k rows.
CREATE INDEX idx_fsr_comp_not_null ON fact_so_respondent(comp_usd) WHERE comp_usd IS NOT NULL;

-- bridge_respondent_skill
CREATE INDEX idx_brs_response      ON bridge_respondent_skill(response_id);
CREATE INDEX idx_brs_skill         ON bridge_respondent_skill(skill_key);
