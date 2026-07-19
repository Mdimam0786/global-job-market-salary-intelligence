# Phase 10 — Power BI Dashboard Build Specification

**Author:** Md Imamuddin

## About this document

The `.pbix` file for this dashboard is still being finalized and will be added once it's ready, along with screenshots of the finished report. This document is the full build specification — every page, every DAX measure, and every Power Query step needed to build the report in Power BI Desktop. The files below are ready to use:

| Deliverable | File | Status |
|---|---|---|
| DAX measures | `powerbi/dax_measures.dax` | Real, paste-ready DAX |
| Data import script | `powerbi/power_query_import.m` | Real Power Query M |
| Custom theme | `powerbi/theme.json` | Valid, loadable Power BI theme JSON |
| This build spec | (this file) | Page-by-page layout, visual, and interaction plan |

To actually assemble the `.pbix`: open Power BI Desktop → Get Data → Text/CSV → import the four Phase 3 cleaned CSVs (or connect to your own Postgres instance if you ran the Phase 4 DDL) → paste the DAX measures into a new measure table → apply the theme via View → Themes → Browse for themes → follow the page-by-page spec below.

---

## Data Model (Import Mode)

Per Phase 4's design: **three fact tables, not one** — `fact_job_postings`, `fact_levels_compensation`, `fact_so_respondent` — each related to shared `dim_date` and `dim_country` tables (star/galaxy schema). Relationships:

- `fact_job_postings[date_key]` → `dim_date[date_key]` (many-to-one)
- `fact_job_postings[country_key]` → `dim_country[country_key]` (many-to-one)
- Same pattern for the other two fact tables

**Do not** create a relationship directly between the three fact tables — they connect only through shared dimensions, never to each other. This is the Power BI equivalent of the "don't merge the three populations" rule from Phase 3/9.

---

## Page 1: Executive Overview

**Purpose:** the 10-second summary for an HR leader or executive who won't read past this page.

- **KPI card row (top, 4 cards):** Total Postings · Average Salary (USD) · Distinct Countries · Remote Share %
- **YoY trend line chart:** Median Salary by work_year, with the `YoY Salary Growth %` measure as a data label — surfaces the 2023→2024 pullback found in Phase 5/7
- **Bar chart:** Median Salary by job_category, sorted descending
- **Map visual:** median salary by country (uses `dim_country` lat/long if enriched, otherwise a filled/shape map by country name)
- **Remote work trend line:** Remote/Hybrid/In-person share by year — this is the single most dramatic finding in the whole project (54%→24%) and deserves prominent placement, not a buried secondary page
- **Bookmark:** "Focus: Remote Trend" bookmark that cross-highlights the remote line chart and hides the map temporarily (Bookmarks pane → capture current state → assign to a button)

## Page 2: Salary Intelligence

- **Slicers:** experience_level, job_category, company_location (synced across this page only, via Sync Slicers pane)
- **Table/matrix:** job_title × experience_level, values = Median Salary, with conditional formatting (data bars) on the value cells
- **Scatter plot:** years_of_experience (Levels.fyi) vs total_yearly_compensation, sized by count — visualizes the r=0.42 correlation from Phase 7 directly
- **KPI card:** `Sample Size Warning` measure displayed conditionally next to any country-level card with n<30 — directly operationalizes the Phase 5 thin-sample caveat in the UI itself, not just a footnote
- **Drill-through page:** right-click a job_category bar → "Drill through to Title Detail" → filtered table of every title in that category with rank

## Page 3: Hiring Trends

- **Area chart:** postings count by job_category over work_year (stacked) — shows the BI/Visualization category's share growth from Phase 5
- **KPI card:** `YoY Postings Growth %`
- **Small multiples:** one mini-chart per job_category showing its individual trend line (Power BI's "Small multiples" formatting option on a line chart, available natively — no custom visual needed)

## Page 4: Skill Intelligence

- **Bar chart:** top 20 skills by `vw_skill_demand` respondent count, split by skill_category via legend
- **Table:** skill association rules (Phase 6/8) — skill_a, skill_b, lift, sortable, filterable by minimum lift
- **Field parameter:** a field parameter toggling the bar chart's x-axis between "Language," "Database," "Platform," "Tool" categories via a single slicer instead of four separate pages — real Power BI feature (Modeling → New Parameter → Fields)
- **Tooltip page:** custom tooltip page showing a skill's top 3 co-occurring skills when hovering over its bar (Format → Tooltips → set tooltip page)

## Page 5: Industry & Company Analysis

- **Bar chart:** top 15 companies by median comp (Levels.fyi) with `Sample Size Warning` on any company under n=100
- **Table:** company × role_family matrix
- **Drill-through:** company bar → filtered page showing all titles/levels at that company

## Page 6: Geographic Analysis

- **Filled map:** median salary by country, `fact_job_postings`
- **Filled map (second visual, same page):** Levels.fyi city-level comp — placed side by side to visually communicate the "these are different populations" point from Phase 3/9 rather than only stating it in text
- **Slicer:** region/continent (if `dim_country` is enriched with World Bank region data per the Phase 2 future-enhancement note)

## Page 7: Remote Work Analysis

- **Line chart:** remote share by year (repeated from Executive Overview but with full slicer interactivity here)
- **Clustered bar:** median salary by work_setting, split by experience_level — surfaces the "remote doesn't cost you money" finding
- **Card:** `Remote vs Onsite Salary Gap %`

## Page 8: Experience Analysis

- **Column chart:** median salary by experience_level with `Confidence interval` error bars if using a custom visual (or a simple secondary line for P25/P75 as a low-cost native substitute)
- **Table:** experience_level × job_category matrix

## Page 9: Market Forecast

- **Line chart with native Power BI forecasting:** Analytics pane → Forecast → apply to the Median Salary by work_year line. Power BI's built-in forecast uses exponential smoothing and is appropriate here **only as a rough directional indicator** — with 5 annual data points, any forecast has wide confidence bands and should be labeled as such on the visual (Format → Analytics → Forecast → ensure confidence interval shading is ON, not hidden)
- **Explicit caption/text box on this page:** "Forecast based on 5 annual observations — treat as directional, not precise" — stated in the report itself, not just in project documentation, since this is the page most likely to be over-trusted by a viewer

## Page 10: ML Predictions

- **Table:** salary model comparison (from Phase 8's `salary_model_comparison.csv`) imported as a small static table
- **Bar chart:** feature importance (`salary_feature_importance.csv`)
- **Card:** best model R² (0.308) with a text box explicitly noting "explains ~31% of salary variance — see ML report for full caveats" rather than presenting the number without context

---

## Global Interaction Features

- **Navigation buttons:** a left-side nav bar (Insert → Buttons → Blank, one per page, grouped and duplicated across all pages via Format → Selection pane copy/paste) — real Power BI pattern, not a custom visual
- **Field parameters:** used on Page 4 (skill category toggle) — Power BI's genuine 2022+ feature, not a workaround
- **Drill-through:** configured on Pages 2 and 5, as described above
- **Bookmarks:** Executive Overview's "Focus: Remote Trend" bookmark, plus a "Reset Filters" bookmark on every page (Bookmarks pane → capture all visuals, all pages → set as the button beside each nav bar)
- **Dynamic tooltips:** custom tooltip page for Page 4's skill bars

## What Is NOT Included, and Why

- **QoQ growth:** no quarterly data exists (see `dax_measures.dax` header note) — including this would mean fabricating quarters
- **Drill-down (hierarchy-based, e.g. Country → State → City) on `fact_job_postings`:** the primary dataset only has country-level location, no state/city breakdown — drill-down is only meaningful on the Levels.fyi city-level data (Page 6), and is scoped there specifically rather than claimed project-wide
