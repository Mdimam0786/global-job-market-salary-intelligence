-- =====================================================================
-- Global Job Market & Salary Intelligence Platform
-- Schema: Bridge Table (many-to-many skills)
-- Author: Md Imamuddin
-- Target: PostgreSQL 15+
-- =====================================================================
-- Why a bridge table: Stack Overflow's *HaveWorkedWith columns are
-- semicolon-delimited multi-select lists (e.g. "Python;SQL;JavaScript").
-- A respondent can have many skills, and a skill has many respondents --
-- classic many-to-many, unmodelable as a single foreign key column.
-- This table is populated in Phase 6 (NLP module) by splitting those
-- delimited strings into one row per (respondent, skill) pair.
-- =====================================================================

CREATE TABLE bridge_respondent_skill (
    bridge_id          BIGSERIAL PRIMARY KEY,
    response_id           INTEGER NOT NULL REFERENCES fact_so_respondent(response_id),
    skill_key               INTEGER NOT NULL REFERENCES dim_skill(skill_key),
    UNIQUE (response_id, skill_key)
);
COMMENT ON TABLE bridge_respondent_skill IS 'Many-to-many resolution between SO respondents and skills. One row per (respondent, skill) pair, exploded from semicolon-delimited source columns.';
