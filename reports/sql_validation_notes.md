# SQL Analytics Layer — Validation Notes

**Author:** Md Imamuddin

## Why validation methodology matters here

A live PostgreSQL server wasn't available while writing this SQL layer, so every query was tested and confirmed correct one of three ways instead of just writing untested SQL and calling it done:

| Method | Used for | Why |
|---|---|---|
| **Executed directly against SQLite 3.45** (loaded with the real cleaned CSVs) | All CTEs, window functions (`RANK`, `DENSE_RANK`, `PERCENT_RANK`, `LAG`), joins, aggregations | SQLite 3.25+ supports standard window functions and CTEs — genuinely the same logic as Postgres for these constructs |
| **Cross-checked against pandas as ground truth** | Any query using `PERCENTILE_CONT(...) WITHIN GROUP` | SQLite doesn't implement `PERCENTILE_CONT` — this is valid ANSI SQL / Postgres syntax (9.4+), so the query text is correct Postgres, but was validated by confirming pandas' `.median()`/`.quantile()` on the same grouping produces matching numbers, since both use the same interpolation method |
| **Syntax-reviewed only, not executed** | Materialized view (`CREATE MATERIALIZED VIEW`), stored procedure (`CREATE FUNCTION ... LANGUAGE plpgsql`) | These features use PostgreSQL-specific syntax that SQLite cannot run, and no live PostgreSQL server was available to run them either. The underlying SELECT logic matches queries that were already tested and confirmed working, so the logic is reliable — but the materialized view/stored procedure wrapper syntax itself was not executed anywhere, and that gap is flagged here rather than implied to be equally tested. |

## Results summary (from executed queries)

All figures below matched the corresponding Phase 5 EDA findings exactly, which is itself a useful cross-check that the SQL layer and the earlier pandas-based EDA agree:

- **Remote work share by year**: 49.3% (2020) → 54.3% (2021) → 53.4% (2022) → 31.3% (2023) → 23.6% (2024) — identical to Phase 5
- **Top skills by respondent count**: JavaScript (37,492, 62.5%), HTML/CSS (31,816, 53.0%), Python (30,719, 51.2%) — identical to Phase 6
- **Country salary ranking**: US → Canada → Australia → UK → Germany → France → Spain — identical to Phase 5
- **Stored-procedure logic spot check**: `get_salary_benchmark('Data Engineering', 'Senior', 150000)` → median $150,000, 51.4th percentile, verdict "within typical market range" — manually reproduced in pandas and confirmed correct

## Files in this phase

| File | Contents |
|---|---|
| `sql/analysis_queries/01_business_kpis.sql` | 5 business-question-driven queries using window functions, CTEs, and percentile analysis |
| `sql/views/01_analytical_views.sql` | 5 reusable views wrapping the KPI queries for Power BI consumption |
| `sql/procedures/01_materialized_view_and_procedure.sql` | 1 materialized view + 1 parameterized stored function (syntax-reviewed, not executed — see above) |
