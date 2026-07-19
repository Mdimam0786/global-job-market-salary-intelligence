// =====================================================================
// Global Job Market & Salary Intelligence Platform
// Power Query M — Data Import & Transformation
// Author: Md Imamuddin
// =====================================================================
// Two supported import paths, since the Phase 4 PostgreSQL schema was
// designed as a reference target but a live Postgres connection wasn't
// used for this build:
//
//   PATH A (recommended if you ran the Phase 4 DDL against your own
//   Postgres instance): connect Power BI directly to Postgres using
//   Get Data > PostgreSQL database, point at the star schema tables,
//   and skip the M code below entirely -- Power BI generates its own
//   native query.
//
//   PATH B (works immediately, no database needed): import the Phase 3
//   cleaned CSVs directly. The M code below implements this path, plus
//   the type-casting and column-renaming needed to match the DAX
//   measures in dax_measures.dax.
// =====================================================================

let
    // ---- fact_job_postings (primary source) ----
    Source_JobsFact = Csv.Document(
        File.Contents("C:\PowerBI\GlobalJobMarket\jobs_fact_clean.csv"),
        [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    JobsFact_Headers = Table.PromoteHeaders(Source_JobsFact, [PromoteAllScalars=true]),
    JobsFact_Typed = Table.TransformColumnTypes(JobsFact_Headers, {
        {"job_id", Int64.Type},
        {"work_year", Int64.Type},
        {"job_title", type text},
        {"job_category", type text},
        {"salary_in_usd", type number},
        {"salary_is_outlier", type logical},
        {"experience_level", type text},
        {"employment_type", type text},
        {"work_setting", type text},
        {"company_size", type text},
        {"company_location", type text},
        {"employee_residence", type text},
        {"source_dataset", type text}
    })
in
    JobsFact_Typed


// =====================================================================
// Query 2: fact_levels_compensation
// =====================================================================
let
    Source_Levels = Csv.Document(
        File.Contents("C:\PowerBI\GlobalJobMarket\levels_fyi_clean.csv"),
        [Delimiter=",", Columns=25, Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    Levels_Headers = Table.PromoteHeaders(Source_Levels, [PromoteAllScalars=true]),
    Levels_Typed = Table.TransformColumnTypes(Levels_Headers, {
        {"record_id", Int64.Type},
        {"company", type text},
        {"title", type text},
        {"total_yearly_compensation", type number},
        {"base_salary", type number},
        {"stock_grant_value", type number},
        {"bonus", type number},
        {"years_of_experience", type number},
        {"years_at_company", type number},
        {"city", type text},
        {"region", type text},
        {"country", type text},
        {"total_comp_is_outlier", type logical}
    })
in
    Levels_Typed


// =====================================================================
// Query 3: fact_so_respondent (skills + salary views merged for import --
// Power BI relates them back out via the bridge table at the model layer)
// =====================================================================
let
    Source_SOSalary = Csv.Document(
        File.Contents("C:\PowerBI\GlobalJobMarket\so_salary_clean.csv"),
        [Delimiter=",", Columns=20, Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    SOSalary_Headers = Table.PromoteHeaders(Source_SOSalary, [PromoteAllScalars=true]),
    SOSalary_Typed = Table.TransformColumnTypes(SOSalary_Headers, {
        {"ResponseId", Int64.Type},
        {"Country", type text},
        {"EdLevel", type text},
        {"DevType", type text},
        {"ConvertedCompYearly", type number},
        {"comp_is_outlier", type logical},
        {"below_sanity_floor", type logical}
    })
in
    SOSalary_Typed


// =====================================================================
// Query 4: dim_date (generated, not imported -- grain is a small,
// known set of years, so generating it in M avoids a trivial extra
// CSV file for 5 rows)
// =====================================================================
let
    Years = List.Numbers(2020, 5),  // 2020..2024, matches Phase 3 work_year range
    ToTable = Table.FromList(Years, Splitter.SplitByNothing(), {"work_year"}),
    Typed = Table.TransformColumnTypes(ToTable, {{"work_year", Int64.Type}}),
    AddDateKey = Table.AddColumn(Typed, "date_key", each [work_year], Int64.Type),
    AddDecade = Table.AddColumn(AddDateKey, "decade", each Number.ToText(Number.RoundDown([work_year] / 10) * 10) & "s", type text),
    AddIsCurrent = Table.AddColumn(AddDecade, "is_current_year", each [work_year] = List.Max(Years), type logical)
in
    AddIsCurrent
