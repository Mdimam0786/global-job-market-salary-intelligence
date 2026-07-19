# Technical Design Document

**Author:** Md Imamuddin

## 1. Why a Galaxy Schema, Not a Single Star

Three independently collected datasets went into this project, each with a different population, granularity, and collection method. Merging them into one fact table would mean either dropping columns that don't overlap or filling in missing columns with guesses — neither is acceptable. Instead, each dataset has its own fact table, connected through shared dimensions (country, date) where the meaning genuinely lines up. There's no forced relationship between the fact tables themselves.

## 2. Why the Date Dimension Is Year-Level, Not Day-Level

All three sources are annual snapshots or surveys — there's no daily transaction data anywhere in this project. A day-level date table would suggest a precision the data doesn't have, and it would also break Power BI's built-in time intelligence functions, which expect a real calendar. Year-over-year calculations are built directly against the year field instead.

## 3. Why Outliers Are Flagged, Not Removed

Salary data naturally has a long right tail — senior engineers, executives, and equity-heavy compensation packages are real, not data errors. Removing them would bias every average toward the middle and misrepresent the market. Instead, outliers are flagged with a boolean column, and each report or dashboard decides whether to include or exclude them for its specific purpose.

## 4. Why Permutation Importance Instead of SHAP

SHAP wasn't available during part of development. Permutation importance was used instead — it answers a related but narrower question ("how much does shuffling this feature hurt model performance") without giving per-prediction explanations or interaction effects the way SHAP does. This is noted directly in `reports/ml_analysis.md` as a real limitation, not treated as an equivalent substitute.

## 5. Why scikit-learn Gradient Boosting Instead of XGBoost or LightGBM

Same reasoning — XGBoost and LightGBM weren't available at the time. Scikit-learn's Gradient Boosting is the same general approach (boosted decision trees) but slower and has fewer tuning options at scale. Results are comparable in kind, though not benchmarked against what XGBoost or LightGBM would produce.

## 6. Why Class Imbalance Wasn't Fully Corrected in the Classification Models

The experience-level and remote-work prediction models were built to honestly reflect the data as it is, including its imbalance (Senior roles make up 66% of the dataset, and In-person roles make up another 66%). Accuracy is reported alongside per-class scores rather than applying class weighting or oversampling just to make the headline number look better. A production version of this model would apply one of those techniques.

**Update:** while building the Streamlit companion app, a bug was found in the original classification script — a `ColumnTransformer` step was missing a setting (`remainder="passthrough"`) that caused the salary feature to be silently dropped from training, even though it was listed as a feature in the code and in the report. This was fixed in `src/ml/classification_models.py`. After the fix, accuracy improved from 67.6% to 70.1% for experience-level prediction and from 67.9% to 69.0% for remote-work prediction, with noticeably better results for the smaller classes in each case. The class imbalance issue is still real after the fix, just less severe than it first appeared.

## 7. Why SQL Was Tested With SQLite Instead of PostgreSQL

A live PostgreSQL server wasn't available during part of development. SQLite supports the same CTEs and window functions used throughout the SQL layer, so those queries were tested directly and produced correct results. `PERCENTILE_CONT` (used for calculating medians) isn't supported in SQLite, so that logic was checked by comparing it against the same calculation done in pandas, confirming the two matched. The materialized view and stored procedure use PostgreSQL-only features with no SQLite equivalent — those were checked for correct syntax but not executed. See `reports/sql_validation_notes.md` for full details.

## 8. Why There's No Power BI File (.pbix) Included

Power BI Desktop is a Windows and Mac application and can't be installed or run in every development environment. Instead, this project includes the actual DAX measures, Power Query M code, and a ready-to-use theme file — everything needed to build the report is specified precisely enough to recreate it without guesswork.

## 9. Open Items for a Future Version

- Build a shared mapping between the three datasets' different job title systems (`dim_role_family` is designed for this but not fully populated)
- Apply class balancing (such as SMOTE or class weights) to the two classification models
- Add city-level cost-of-living data (not available in open datasets at the time of writing)
- Run the full pipeline against a live PostgreSQL server and Power BI Desktop to complete the remaining validation steps
