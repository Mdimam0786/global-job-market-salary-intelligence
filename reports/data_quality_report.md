# Data Quality Report — Phase 3

**Author:** Md Imamuddin

**Pipeline run date:** 2026-07-09
**Scripts:** `src/etl/clean_jobs_data.py`, `src/etl/clean_levels_fyi.py`, `src/etl/clean_so_survey.py`

---

## 1. Summary of Outputs

| Output file | Rows | Cols | Role |
|---|---|---|---|
| `data/processed/jobs_fact_clean.csv` | 14,199 | 15 | Primary fact table — job postings, salary, role, location |
| `data/processed/levels_fyi_clean.csv` | 62,642 | 25 | Company/level compensation benchmarking |
| `data/processed/so_skills_clean.csv` | 65,437 | 18 | Full SO survey subset — skills/tech-stack demand (NLP source) |
| `data/processed/so_salary_clean.csv` | 23,435 | 20 | SO survey respondents with usable compensation data only |

Three fact-shaped outputs, not one merged table. This was a deliberate call — see §4.

---

## 2. Per-Dataset Findings

### 2.1 `jobs_in_data_2024` (primary)
- **Zero missing values** across all 12 source columns — this dataset was already survey-clean at the source.
- **5,493 exact duplicate rows (38.7%).** Investigated rather than dropped: with only 12 low-cardinality categorical/binned columns and 14,199 rows, collisions between genuinely distinct respondents are statistically expected, not a sign of a scrape error. Verified by comparing the `job_title` distribution with and without duplicates — the maximum share shift was 2.55 percentage points, consistent with duplicates being real rows rather than an artifact. **Decision: keep all rows.**
- **261 salary outliers flagged** (1.84%) via IQR on `salary_in_usd`. Not removed — flagged in a `salary_is_outlier` column so EDA/ML/Power BI can decide whether to filter.
- Added `job_id` surrogate key (source has none) and `source_dataset` provenance column.

### 2.2 `Levels_Fyi_Salary_Data`
- **Zero exact duplicate rows.**
- `location` field (e.g. `"Seattle, WA"` vs `"Amsterdam, NH, Netherlands"`) parsed into `city` / `region` / `country` using a comma-count rule. **All 62,642 rows resolved to a country successfully** — no unparseable rows.
- **Gender: 31.2% null. Race: 64.2% null. Education: 51.5% null.** All are optional self-reported fields. **None were imputed** — fabricating demographic data about real survey respondents would misrepresent them, and any chart using these fields must disclose the reduced sample size.
- Dropped 10 pre-computed one-hot dummy columns (`Masters_Degree`, `Race_White`, etc.) — redundant with the single `Education` / `Race` columns already present; keeping both bloats the table without adding information.
- **3,133 compensation outliers flagged** (5.0%) via IQR on `total_yearly_compensation` (max value: $4.98M — plausible for a senior exec/staff+ equity-heavy year, not removed).

### 2.3 Stack Overflow 2024 Developer Survey
- Subset from 114 → 17 relevant columns (role, comp, location, education, tech-stack). Full raw file untouched in `data/raw/` if ever needed.
- `ConvertedCompYearly` is **64.2% null** — it's an optional field, and a "salary" table with two-thirds nulls would corrupt every downstream aggregate. Solved by splitting into two outputs:
  - `so_skills_clean.csv` — all 65,437 respondents, used for skills/tech-stack demand (doesn't need salary to be useful)
  - `so_salary_clean.csv` — 23,435 respondents (35.8%) with both compensation and country present
- **545 rows below a $1,000/yr sanity floor** — almost certainly joke/test responses, not real annual salaries. Flagged (`below_sanity_floor`), not deleted.
- Additional IQR outlier flag applied on top of the sanity floor.

---

## 3. Cross-Dataset Sanity Check

| Source | Median annual comp (USD) |
|---|---|
| `jobs_fact_clean` (data-field roles, global) | $142,000 |
| `levels_fyi_clean` (Big Tech-heavy, mostly US) | $188,000 |
| `so_salary_clean` (all developer roles, global) | $65,000 |

These three numbers are **not inconsistent** — they're three different populations (specialized data roles vs. FAANG-heavy vs. the full global developer base including many lower-cost-of-living countries and junior roles). This is exactly why the three sources are kept as **separate fact tables joined through shared dimensions (country, role, experience)** in the star schema, rather than being unioned into one "salary" column — unioning them would average together three different labor markets and produce a meaningless blended number.

---

## 4. Key Design Decision: Three Fact Tables, Not One

Merging all three sources into a single row-level table was considered and rejected:
- Different populations (data specialists vs. all developers vs. Big Tech employees)
- Different collection methodology and time windows
- Different column shapes (binned salary ranges vs. exact figures vs. total comp with equity breakdown)

Instead, the **star schema** (Phase 4) will connect them through shared conformed dimensions — `Dim_Country`, `Dim_ExperienceLevel`, `Dim_Date` — so Power BI can slice each fact table independently or compare them side-by-side without ever averaging incompatible numbers together.

---

## 5. Outstanding Items for Phase 4 (Schema Design)

- Standardize experience-level labels across all three sources (each uses different category names/granularity)
- Map `DevType` (SO) and `job_category`/`job_title` (jobs_fact) into a shared `role_family` dimension
- Currency normalization already done in-source (`salary_in_usd`, `ConvertedCompYearly`) — verify FX methodology per source before treating as directly comparable
