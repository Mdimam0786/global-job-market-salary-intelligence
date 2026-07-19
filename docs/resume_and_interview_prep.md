# Resume Bullet Points & Interview Preparation

**Author:** Md Imamuddin

## Resume Bullet Points (quantified, from actual project results)

- Built an end-to-end data platform integrating 3 real public datasets (142,278 combined rows) into a PostgreSQL galaxy schema (3 fact tables, 9 dimensions), with full ETL validation and a documented data-quality report
- Wrote 15+ production SQL scripts (CTEs, window functions, materialized views) validated against a live database, delivering business KPIs including country/category salary benchmarking and a parameterized salary-lookup stored function
- Conducted statistical analysis (hypothesis testing, ANOVA, regression) identifying that job category and experience level each independently explain ~14% of salary variance (η²), and that a 4-feature regression model achieves R²=0.31 on held-out data
- Built and evaluated 5 machine learning models (salary prediction, experience-level classification, remote-work classification, clustering, skill recommendation), reporting honest per-class performance rather than misleading aggregate accuracy
- Performed NLP-based skill extraction and market-basket association analysis across 181 distinct skills and 967,209 (respondent, skill) pairs, powering a skill-recommendation feature validated against real-world tech ecosystem patterns
- Designed a 10-page Power BI dashboard specification with DAX time-intelligence measures, drill-through, bookmarks, and field parameters
- Documented 101 grounded business insights, including identifying two likely data-collection artifacts in the source survey that could have been mistakenly reported as real market trends

## Interview Questions to Prepare For

**"Walk me through your project."**
Lead with the business questions (salary drivers, skill demand, remote trends), then the pipeline (3 real datasets → cleaning → star schema → SQL/ML/BI), then 2-3 headline findings (remote work collapse, country as strongest salary predictor, skill breadth sweet spot).

**"Why didn't you just merge all three datasets into one?"**
Different populations, different collection methods, different medians ($142K/$188K/$65K). Merging would silently average three different labor markets into a number that describes none of them. This is your strongest "I understand data semantics, not just data plumbing" answer.

**"Your classification model got 70% accuracy — that's decent, right?"**
Better than it first sounds, but still walk through the per-class F1 scores — Senior/In-person (the majority classes) still dominate recall, and Executive/Hybrid (the smallest classes) are still hardest to predict. This is your strongest "I don't let a single metric fool me" answer, and one of the most interview-relevant moments in the whole project.

**"Tell me about a bug you found in your own project."**
Building the Streamlit companion app required re-implementing the Phase 8 classification pipeline from scratch. Doing so surfaced a real bug: a missing `remainder="passthrough"` on a `ColumnTransformer` had been silently dropping the `salary_in_usd` feature the whole time, despite it being listed as used in both the code and the report. Fixing it improved accuracy from 67.6% to 70.1% and nearly quadrupled Entry-level recall. Strong story for why independent re-implementation catches things code review alone might miss -- and why the fix and the original wrong numbers are both still in the report, not quietly replaced.

**"What would you do differently with more time/resources?"**
Point to the Technical Design Document's open items: conformed role-family mapping across sources, class imbalance correction, live PostgreSQL/Power BI validation, city-level cost-of-living enrichment.

**"How did you handle the outliers?"**
Flagged via IQR, never removed. Salary data has a legitimate long right tail (executives, equity-heavy comp) — removing it would bias the whole dataset toward the median.

**"You didn't have XGBoost/SHAP/Power BI Desktop — doesn't that undermine the project?"**
No — it's an honest constraint of the build environment, documented at every point it mattered, with the actual capability gap named each time (permutation importance vs. SHAP; scikit-learn GBM vs. XGBoost; SQLite-validated SQL vs. live Postgres). The judgment about *when* a substitute is adequate and when to flag a real limitation is itself the skill being demonstrated.

**"What's the single most interesting finding?"**
Probably the remote-work collapse (54%→24% in 3 years) or the skill-breadth "sweet spot" (pay peaks at 6-8 languages known, then declines) — both are non-obvious, both are directly actionable, and both survived a skeptical second look.

**"How confident are you in the salary predictions?"**
Not very, and say so: R²=0.31 means 69% of salary variance is unexplained by the four features used. That's an honest, defensible number — far better to own that limitation than to imply the model is more predictive than it is.
