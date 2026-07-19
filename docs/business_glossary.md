# Business Glossary

**Author:** Md Imamuddin

**Outlier flag** — a boolean column (`salary_is_outlier`, `total_comp_is_outlier`, `comp_is_outlier`) marking rows outside 1.5×IQR of their distribution. Never removes data; lets downstream consumers (SQL, Power BI, ML) decide whether to include or exclude.

**Sanity floor** — a $1,000/year threshold below which Stack Overflow compensation responses are flagged as likely data-entry errors or joke responses, not deleted.

**Source dataset / provenance** — every fact row is tagged with which of the three original sources it came from. Critical because the three sources are never blended (see below).

**"Don't blend the three sources" rule** — `fact_job_postings`, `fact_levels_compensation`, and `fact_so_respondent` represent three different populations (specialized data roles, Big Tech-heavy, and the general global developer base respectively) with materially different median salaries. They are connected through shared dimensions (country, date) but never unioned into a single "salary" figure, because doing so would silently average incompatible labor markets.

**Job category vs. title vs. role family** — `job_title` is the verbatim source string. `job_category` is a 10-value taxonomy specific to the primary dataset. `title` in Levels.fyi is a separate, coarser 8-value taxonomy. `dim_role_family` (Phase 4 schema) is the intended conformed mapping across all three — scaffolded but not fully populated (see Technical Design Document's open items).

**Experience level bands** — Entry-level, Mid-level, Senior, Executive. Ordered categorically; sort order enforced in the model so charts/DAX don't default to alphabetical order.

**Remote/Hybrid/In-person (work_setting)** — self-reported at the time of the job posting/survey response, not verified against any external source.

**Lift (skill association)** — from market-basket analysis: `lift > 1` means two skills co-occur more often than random chance would predict (a genuine affinity); `lift ≤ 1` means no meaningful relationship beyond both being independently common.

**η² (eta-squared)** — effect size for ANOVA: the share of total variance explained by group membership. Reported per Cohen's convention (small <0.06, medium 0.06–0.14, large ≥0.14) rather than relying on p-value alone, since statistical significance and practical importance are different questions (see `reports/statistical_analysis.md`).

**Silhouette score** — cluster-quality metric ranging roughly -1 to 1; higher means better-separated clusters. Scores in this project (0.19–0.22) are modest, meaning the job clusters found are gradual/overlapping segments, not sharply distinct archetypes — stated plainly rather than oversold.

**Permutation importance** — a global feature-importance method: shuffle one feature, measure how much model performance drops. Used here as a stated substitute for SHAP (unavailable in the build environment) — it answers a similar question at the aggregate level but does not provide per-prediction explanations the way SHAP does.
