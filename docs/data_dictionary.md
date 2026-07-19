# Data Dictionary

**Author:** Md Imamuddin

## fact_job_postings (primary, 14,199 rows)

| Column | Type | Description |
|---|---|---|
| job_id | INTEGER (PK) | Surrogate key, generated in Phase 3 (source has no natural ID) |
| work_year | SMALLINT | Survey year, 2020-2024 |
| job_title | VARCHAR | Verbatim title from source |
| job_category | VARCHAR | 10-category taxonomy (Data Science, ML/AI, Data Engineering, etc.) |
| experience_level | VARCHAR (ordered) | Entry-level < Mid-level < Senior < Executive |
| employment_type | VARCHAR | Full-time, Part-time, Contract, Freelance |
| work_setting | VARCHAR | Remote, Hybrid, In-person |
| company_size | VARCHAR (ordered) | S < M < L |
| company_location | VARCHAR | Country where the company is located |
| employee_residence | VARCHAR | Country where the employee resides |
| salary_in_usd | NUMERIC | Annual salary, normalized to USD by the source |
| salary_is_outlier | BOOLEAN | IQR-based flag (Phase 3) -- not removed, for reporting-layer filtering |
| source_dataset | VARCHAR | Always "jobs_in_data_2024" -- provenance tracking |

## fact_levels_compensation (62,642 rows)

| Column | Type | Description |
|---|---|---|
| record_id | INTEGER (PK) | Surrogate key |
| company | VARCHAR | Employer name |
| title | VARCHAR | One of 8 broad tech titles (coarser than job_category above) |
| city / region / country | VARCHAR | Parsed from the source's combined `location` field (Phase 3) |
| total_yearly_compensation | NUMERIC | Total comp including equity/bonus |
| base_salary / stock_grant_value / bonus | NUMERIC | Comp breakdown |
| years_of_experience / years_at_company | NUMERIC | Self-reported |
| Education / gender / Race | VARCHAR | Optional self-reported fields -- 31-64% null, never imputed |
| total_comp_is_outlier | BOOLEAN | IQR-based flag |
| source_dataset | VARCHAR | Always "levels_fyi" |

## fact_so_respondent (23,435 rows with compensation; skills view has all 65,437)

| Column | Type | Description |
|---|---|---|
| ResponseId | INTEGER (PK) | Source respondent ID |
| Country, EdLevel, DevType, Employment, RemoteWork, OrgSize, Industry | VARCHAR | Respondent attributes |
| YearsCodePro | VARCHAR | Note: contains non-numeric values ("Less than 1 year") -- parse before numeric use |
| ConvertedCompYearly | NUMERIC | USD-normalized comp -- NULL for ~64% of respondents (optional field) |
| below_sanity_floor | BOOLEAN | Flags comp < $1,000/yr (likely joke/test responses) |
| comp_is_outlier | BOOLEAN | IQR-based flag |

## dim_skill (181 rows) / bridge_respondent_skill (967,209 rows)

| Column | Description |
|---|---|
| skill_key, skill_name, skill_category | 5 categories: Language, Database, Platform, Webframe, Tool |
| bridge_id, response_id, skill_key | One row per (respondent, skill) pair, exploded from semicolon-delimited source columns |

## Derived Model Outputs

| File | Description |
|---|---|
| skill_association_rules.csv | 780 skill pairs with support/confidence/lift |
| job_clusters.csv | KMeans cluster assignment per job_id (k=8) |
| salary_model_comparison.csv, salary_feature_importance.csv | ML model results |
