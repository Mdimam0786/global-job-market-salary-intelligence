# Phase 6 — NLP & Skill Extraction

**Author:** Md Imamuddin

## Scope and an honest limitation up front

The original project brief lists "extract skills from job descriptions" as an NLP task. As flagged in the Phase 2 honesty audit, **none of our three sources contain free-text job description fields** — `jobs_fact` and Levels.fyi never had them, and Stack Overflow is a structured survey, not a set of postings. Rather than fabricate description text to run NER against, this phase does the NLP-adjacent work the data actually supports:

1. Structured skill extraction from Stack Overflow's semicolon-delimited multi-select columns → skill bridge table
2. Skill co-occurrence / association rule mining (market-basket technique)
3. TF-IDF over job titles to find category-distinguishing terms
4. Keyword-based technology trend analysis over time (job titles)
5. Skill frequency visualization (custom-built word cloud)

---

## 1. Skill Bridge Table

`src/etl/build_skill_bridge.py` unpivoted the 5 multi-select columns into:

- **`dim_skill.csv`** — 181 distinct skills across 5 categories (Language: 49, Webframe: 36, Database: 35, Tool: 34, Platform: 27)
- **`bridge_respondent_skill.csv`** — 967,209 (respondent, skill) pairs across 60,009 respondents (a subset of the 65,437 total — some respondents skipped all 5 skill questions)

This directly populates the `bridge_respondent_skill` and `dim_skill` tables designed in Phase 4's schema.

---

## 2. Skill Co-occurrence & Association Analysis

Applied market-basket analysis (support / confidence / lift) to the top 40 most common skills (≥500 respondents each, to keep lift estimates statistically stable — rare skills produce unstable ratios). Full results in `skill_association_rules.csv` (780 pairs).

**Top skill affinities by lift** (co-occurring far more than chance would predict):

| Skill A | Skill B | Lift | Interpretation |
|---|---|---|---|
| NuGet | Visual Studio Solution | 3.66 | The .NET ecosystem cluster is the strongest affinity in the dataset |
| C# | NuGet | 3.40 | Confirms the .NET stack clusters tightly |
| Maven | Gradle | 2.98 | Java build-tool overlap — many devs know both, fewer know neither |
| Express | Next.js | 2.96 | Full-stack JS devs commonly span both server and meta-framework layers |
| C | C++ | 2.90 | Classic systems-programming pairing, as expected |
| Next.js | React | 2.69 | Confirms Next.js is overwhelmingly a React-ecosystem tool, not standalone |
| Express | Node.js | 2.67 | Sanity-check pairing — Express is a Node.js framework, this *should* be near-total overlap, and 88% confidence (A→B) confirms it |

The Express→Node.js pairing (88% confidence) is a useful **validation check**: since Express is built on Node.js, near-total co-occurrence is expected, and seeing that confirms the extraction pipeline is working correctly rather than producing noise.

**Business use:** this is the statistical backbone for a genuine skill-recommendation feature (Phase 5's ML module, upcoming) — "developers who know X also tend to know Y" translates directly into "if you're learning X, Y is a natural next skill."

---

## 3. TF-IDF on Job Titles by Category

Ran TF-IDF (unigrams + bigrams, English stopwords removed) treating each `job_category`'s concatenated titles as one document.

**Finding, stated honestly:** the top TF-IDF terms per category are near-tautological — "Data Engineering" surfaces `data engineer`, `engineer data`; "Machine Learning and AI" surfaces `learning engineer`, `machine learning`. This is expected and not a failure of the method: `job_category` in the source data was almost certainly derived directly from `job_title` text, so TF-IDF is confirming internal consistency between the two columns rather than revealing a hidden pattern. **This is a legitimate, useful validation result** — it's evidence the category labels are trustworthy and not mis-assigned — but it should not be oversold as a novel discovery.

One category did show a more interesting signal: **"Leadership and Management"** titles score highest not on management terms but on `analytics engineer` and `data manager` — suggesting this category is a mixed bag of individual-contributor-adjacent "analytics engineer" titles alongside true management titles, worth a closer manual look in Phase 7 if `role_family` mapping needs refinement.

---

## 4. Technology Trend Analysis (Keyword-in-Title, by Year)

| Keyword | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| "engineer" | 33.8% | 39.1% | 43.4% | 43.4% | 39.1% |
| "scientist" | 38.0% | 30.0% | 29.0% | 28.2% | 26.3% |
| "machine learning" | 9.9% | 13.7% | 9.4% | 12.9% | 11.5% |
| "analytics" | 0.0% | 3.0% | 4.2% | 3.0% | 3.9% |
| "architect" | 0.0% | 2.5% | 2.8% | 2.5% | 2.9% |
| "ai" | 1.4% | 1.0% | 0.7% | 1.1% | 1.8% |
| "cloud" | 0.0% | 1.5% | 0.1% | 0.2% | 0.2% |
| "bi" | 5.6% | 3.0% | 0.9% | 1.1% | 1.1% |
| **"generative" / "llm"** | **0.0%** | **0.0%** | **0.0%** | **0.0%** | **0.0%** |

**Most notable finding:** despite 2023–2024 being the height of the generative AI/LLM boom in industry press, **zero job titles in this dataset contain "generative" or "LLM"** in any year. Two plausible explanations, stated as alternatives rather than a firm conclusion: (a) job titles are a lagging indicator and haven't caught up to the trend yet, or (b) this survey's respondent base and the way ai-jobs.net aggregates titles doesn't capture emerging AI-native titles well. Either way, this is a genuine, checkable finding — and a good example of a dataset limitation that a text-mining pass surfaces which a simple category count would have missed entirely.

"Engineer" overtaking "Scientist" as the dominant title term (33.8%→39.1% engineer vs. 38.0%→26.3% scientist from 2020 to 2024) is a plausible signal of the field maturing from a research-flavored discipline toward a production/engineering-flavored one — consistent with the industry-wide "MLOps" narrative, though this single keyword measure isn't proof on its own.

---

## 5. Skill Frequency Visualization

The `wordcloud` package wasn't available for this analysis, so the word cloud was built directly with matplotlib instead: word size scales with respondent count, colors cycle for readability, and layout uses randomized collision-avoidant placement. See `reports/figures/skill_wordcloud.png`.

---

## Summary

| Deliverable | File |
|---|---|
| Skill dimension table | `data/processed/dim_skill.csv` |
| Skill bridge table | `data/processed/bridge_respondent_skill.csv` |
| Skill association rules | `data/processed/skill_association_rules.csv` |
| Skill word cloud | `reports/figures/skill_wordcloud.png` |
| ETL scripts | `src/etl/build_skill_bridge.py`, `src/etl/skill_relationships.py` |
