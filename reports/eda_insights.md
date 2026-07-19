# Exploratory Data Analysis — 100+ Business Insights

**Author:** Md Imamuddin

**Sources:** `fact_job_postings` (14,199 rows, data-specialist roles, global), `fact_levels_compensation` (62,642 rows, Big Tech-heavy), `fact_so_respondent` (23,435 rows with reported comp, all developer roles, global)

All figures below are computed directly from the cleaned Phase 3 outputs — nothing here is estimated or illustrative.

---

## Executive Summary

1. Senior-level data professionals earn a median of **$155,000**, nearly double Entry-level's **$83,171** — experience is the single strongest salary lever in the data-role market.
2. Machine Learning/AI is the highest-paying data job category (**$180,000 median**), ahead of Data Science ($156,400) and Data Engineering ($140,000).
3. The US dominates the global data-job dataset (**87.8%** of rows) and pays a **78% premium** over the UK ($148,300 vs $81,206 median).
4. Remote work's share of postings **collapsed from 54.3% (2021) to 23.6% (2024)** — the clearest "return to office" signal in the data.
5. At Big Tech (Levels.fyi), median total comp is **$216,000**, well above the data-specialist market — but this reflects company selection (FAANG-heavy), not a like-for-like comparison.
6. Across all developers globally (Stack Overflow), median comp is **$65,000** — a reminder that "data scientist salaries" headlines describe a narrow, high-earning slice of the global developer population.
7. Knowing more programming languages correlates with higher pay only up to a point — comp rises through 6–8 languages known, then **plateaus and slightly declines** beyond 8, consistent with generalist breadth outpacing depth after a threshold.
8. Company-size distribution in the primary dataset shifted from a 45/24/31 (Large/Medium/Small) split in 2020 to **96.6% Medium** by 2024 — this is almost certainly a data-collection/methodology artifact of the underlying survey, not a real market shift, and is flagged rather than presented as a genuine trend (see Methodology Caveats).

---

## 1. Salary Trends (data-specialist roles — `fact_job_postings`)

9. Median salary by experience level: Entry-level $83,171 · Mid-level $115,000 · Senior $155,000 · Executive $190,000.
10. Senior professionals outnumber every other level 2.8-to-1 (9,381 of 14,199 rows) — the dataset skews toward experienced respondents.
11. The Entry→Mid step is a **+38%** jump; Mid→Senior is **+35%**; Senior→Executive is **+23%** — the biggest proportional jump in a data career is the first one, out of entry-level.
12. Full-time roles pay a median of $142,200, more than **2.5x** Freelance ($50,000) and **2.6x** Part-time ($54,266) — contract/freelance data roles in this market are not a premium arrangement, contrary to common freelance-economy narratives.
13. Contract roles ($89,444 median) sit between part-time and full-time, but with only 26 data points — too thin to generalize confidently.
14. In-person roles ($144,000 median) slightly out-earn remote roles ($140,358) and substantially out-earn hybrid ($74,000, but n=213 — a small, likely non-representative slice).
15. Medium-sized companies pay a higher median ($144,000) than Large companies ($136,000) in this dataset — counter to the "Big Co pays more" assumption, though see the company-size caveat in §14.
16. Small companies pay markedly less ($75,324 median) — roughly half of Medium/Large.

## 2. Job Category & Role Analysis

17. Ranked by median salary: ML/AI ($180,000) > Data Science & Research ($156,400) > Data Architecture ($150,000) > Cloud/Database ($146,125, n=11, thin sample) > Data Engineering ($140,000) > Leadership/Management ($134,000) > BI/Visualization ($118,100) > Data Analysis ($100,948) > Data Mgmt/Strategy ($85,000) > Data Quality/Ops ($82,000).
18. Data Engineer is the single most common title (3,059 rows), narrowly ahead of Data Scientist (2,910).
19. Data Analyst (2,120) and ML Engineer (1,488) round out the top four titles by volume.
20. Highest-paying specific titles (min. 30 respondents): Director of Data Science ($217,000), Head of Data ($215,000), Applied Scientist ($192,000), Data Science Manager ($190,000), ML Engineer ($188,200).
21. Computer Vision Engineer ($185,000, n=31) and AI Engineer ($166,000, n=93) — the two most "2024-native" AI titles — both out-earn the generic "Data Scientist" title ($151,355).
22. The generic "Data Scientist" title, despite being the 2nd-most common, ranks outside the top 10 by pay — specialization commands a premium over the generalist label.
23. Leadership/Management roles pay less than individual-contributor ML/AI and Data Science roles at the same seniority — in this dataset, the technical ladder out-earns the management ladder at the top end.

## 3. Country & Geographic Analysis

24. US median: $148,300 (n=12,465) — by far the largest and highest-paid market in the dataset.
25. Canada: $140,000 (n=373) — closest to US parity of any country with meaningful volume.
26. Australia: $105,000 (n=51, thin sample).
27. UK: $81,206 (n=623) — a **45% pay gap** versus the US for data roles.
28. Germany: $76,833 (n=96); France: $64,781 (n=59); Spain: $48,585 (n=127) — a clear declining gradient across major EU economies.
29. Spain's median ($48,585) is **less than a third** of the US median for comparable data roles.
30. Cross-checking against Stack Overflow's broader developer population: US comp ($143,000 median) is close to the data-specialist figure, but the UK ($84,076), Germany ($73,036), and France ($53,703) medians are all consistent within a few thousand dollars of the data-specialist numbers — reasonable convergence across two independently-collected sources, which is a good sign of data reliability rather than survey noise.
31. Israel ($113,334) and Switzerland ($111,417) are the two highest-paying non-US developer markets in the Stack Overflow data — both ahead of Australia, Canada, and every EU country shown.
32. Nordic countries (Denmark $89,137, Norway $79,552, Sweden $57,230) show meaningful internal spread — Denmark pays 55% more than Sweden despite regional proximity.
33. Poland ($55,535) sits below Sweden despite being a major and growing tech-outsourcing hub — consistent with cost-of-living-adjusted compensation strategies by employers.

## 4. City-Level Analysis (Levels.fyi, Big Tech)

34. Seattle is the single largest metro by volume (8,701 rows) — a direct reflection of Amazon and Microsoft's headcount concentration there.
35. San Francisco (6,797), New York (4,562), Redmond (2,650), and Mountain View (2,277) round out the top five.
36. Highest median comp by city: Los Gatos ($464,500, n=226) — driven almost entirely by Netflix's headquarters location there.
37. Menlo Park ($306,000) and Mountain View ($261,000) — both Meta/Google-adjacent — rank 2nd and 3rd.
38. Seattle, despite the highest volume, has a comparatively modest median ($220,000) versus Bay Area cities — reflecting Amazon and Microsoft's broader, less compensation-top-heavy leveling compared to Meta/Google/Netflix.
39. San Jose ($207,000) is the lowest of the top-10-by-volume Bay Area cities, despite being geographically central to Silicon Valley.

## 5. Company Analysis (Levels.fyi)

40. Amazon is the single largest employer by volume (8,126 rows), ahead of Microsoft (5,216) and Google (4,330).
41. Facebook/Meta (2,990) and Apple (2,028) round out the top five by volume.
42. Highest-paying company by median comp (min. 100 respondents): Netflix ($468,500) — more than **2.5x** Amazon's typical level and nearly **60% above** the next-highest company, Snap ($365,000).
43. Snap ($365,000), Lyft ($350,000), Stripe ($340,000), and Airbnb ($336,000) fill out the top five — all "hot" late-2010s/2020s tech unicorns rather than legacy Big Tech.
44. Among high-volume employers, Facebook ($294,000 median on 2,990 respondents) pays notably more than same-tier peers Uber ($272,500) and Broadcom ($275,000).
45. Netflix's outlier-high median is consistent with its publicly known all-cash, no-bonus/limited-equity compensation philosophy — the number is not an artifact, it matches known company policy.

## 6. Experience & Tenure Analysis

46. In Levels.fyi, comp climbs steadily with tenure at the same company: <1yr $176,000 → 1–3yr $183,000 → 3–6yr $210,000 → 6–10yr $230,000 → 10+yr $250,000.
47. The 3–6 year tenure band shows the single largest jump (+14.8% over 1–3yr) — consistent with promotion cycles typically landing in year 3–5.
48. Years-of-experience correlates moderately with total comp (r=0.42) — meaningful but far from deterministic; company and role choice clearly matter as much or more.
49. In the Stack Overflow data, years of professional coding experience correlates far more weakly with comp (r=0.14) — a materially different result from Levels.fyi's r=0.42, likely because SO spans far more countries/company tiers where experience-to-pay translation is less standardized than at the Big Tech firms Levels.fyi covers.

## 7. Remote Work Analysis

50. Data-role remote share by year: 2020 49.3% → 2021 54.3% → 2022 53.4% → 2023 31.3% → 2024 23.6%.
51. The drop from 2022 to 2023 (53.4%→31.3%, a 22-point fall) is the single largest year-over-year shift of any metric in this dataset — the clearest quantitative evidence of the broad "return to office" push across the industry.
52. Remote roles do not carry a salary discount in the data-role dataset — remote ($140,358) and in-person ($144,000) medians are within 3% of each other.
53. In the Stack Overflow developer population, Remote work actually pays the highest median ($75,000) versus Hybrid ($66,592) and In-person ($44,586) — the opposite ranking from the pattern in Levels.fyi/jobs_fact, likely because SO's "in-person" respondents skew toward markets/roles with generally lower pay, not because remote work itself commands a premium.
54. Hybrid arrangements show the smallest sample and the most erratic numbers across all three sources — treat hybrid-specific comp claims with the most caution of the three remote categories.

## 8. Skills & Technology Demand (Stack Overflow, NLP-sourced)

55. Top 5 languages by respondents: JavaScript (37,492), HTML/CSS (31,816), Python (30,719), SQL (30,682), TypeScript (23,150).
56. Python and SQL — the two languages most directly relevant to data roles — are each known by roughly **47%** of all 65,437 respondents, confirming they are baseline, not specialized, skills in the modern developer market.
57. Bash/Shell (20,412), Java (18,239), C# (16,318), and C++ (13,827) round out the top nine most broadly known languages.
58. Top databases: PostgreSQL (25,536) has overtaken MySQL (21,099) as the most-used database among respondents who report any DB — a notable shift from the historical MySQL-dominant narrative.
59. SQLite (17,365) ranks third — likely reflecting its ubiquity in local/dev environments rather than production usage at scale.
60. MongoDB (13,007) is the highest-ranked NoSQL database, ahead of Redis (10,463) — document stores currently out-rank key-value stores in reported usage.
61. Top cloud platforms: AWS (22,191) leads by a wide margin, with Azure (12,850) second and Google Cloud (11,605) third — AWS's lead over Azure is roughly **73%**.
62. Cloudflare (6,974) and Firebase (6,443) — both often overlooked in "big 3 cloud" narratives — have meaningful independent adoption, likely reflecting the rise of edge/serverless architectures outside the traditional cloud giants.
63. Top web frameworks: Node.js (19,772) and React (19,167) are nearly tied for first — the two pillars of the modern JavaScript stack.
64. Next.js (8,681) already outranks the long-established Angular (8,306) — a signal of React's meta-framework ecosystem consolidating around Next.js specifically.
65. Top tools: Docker (29,219) is the single most-adopted tool of any kind in the entire skills dataset — ahead of even npm (26,866), the default Node.js package manager.
66. Kubernetes (10,503) trails Docker by nearly 3-to-1 — container orchestration adoption significantly lags basic containerization, suggesting many teams containerize without yet operating at Kubernetes-justifying scale.

## 9. Skill Premium & Combination Analysis

67. Among languages with 200+ respondents reporting salary, the highest-paying are niche/legacy languages: Erlang ($100,636), Elixir ($96,000), Clojure ($95,541), Ruby ($90,221), Perl ($90,000) — all functional or older languages with smaller, more senior/specialized talent pools.
68. Scala ($88,619) and Apex ($82,500, Salesforce-specific) also rank in the top ten — both are "enterprise-niche" languages with limited but well-paid talent pools.
69. Mainstream, high-volume languages (JavaScript, Python, Java) do **not** appear in the top-15 highest-paid list — broad adoption correlates with lower relative pay premium, a classic supply/demand signature.
70. R ($76,307, n=4,792) — the language most associated with classical statistics/data science — pays above Go, Rust, and Swift despite its academic reputation, likely reflecting senior researcher/scientist usage.
71. Comp rises with the number of languages known up to a point: 0–2 langs $61,866 → 3–4 $64,248 → 5–6 $68,740 → 7–8 $70,063 — then **declines** to $64,444 for 9+ languages.
72. The 7–8 language "sweet spot" pays **13.3% more** than the 0–2 language baseline — but the drop-off beyond 8 suggests a point of diminishing (even negative) returns to breadth over depth, worth flagging for the skill-recommendation ML model in Phase 5's downstream work.

## 10. Education & Credential Analysis

73. In Levels.fyi: PhD holders earn the highest median ($253,000), a **62% premium** over Bachelor's-only ($156,000).
74. Master's degree holders ($195,000) sit between Bachelor's and PhD, roughly at the market's overall median.
75. "Some College" ($173,000) and "Highschool" ($162,500) both slightly outperform pure Bachelor's-only respondents in Levels.fyi — a counterintuitive result likely explained by these respondents having long, senior tenures that compensate for the credential gap (self-selection: people without degrees who reach Big Tech tend to be unusually accomplished).
76. In the Stack Overflow population (a much broader, non-Big-Tech-skewed sample), the credential gradient is smoother and more intuitive: Professional degree ($79,962) > Master's ($68,203) > Bachelor's ($67,129) > Associate's ($60,147) > some college ($59,288) > secondary school ($45,111) > primary school ($36,088).
77. The PhD/Master's comp premium is far larger in Big Tech (Levels.fyi, +30% PhD-over-Master's) than in the general developer population (SO's "professional degree" category, which includes PhD, is only +17% over Master's) — advanced degrees pay off disproportionately more at elite tech employers specifically.

## 11. Compensation Structure Analysis

78. Stock grants make up the largest share of total comp for Software Engineering Managers (24.3% of total comp) among the top 8 titles by volume.
79. Technical Program Managers (17.4%) and Product Managers (16.7%) also carry meaningfully equity-heavy packages.
80. Data Scientists (12.1%) and Solution Architects (10.0%) carry the least equity-weighted packages among the top titles — their comp is more cash/base-driven than product/engineering-management peers.

## 12. Time-Series & Market Evolution

81. Global median salary for data roles rose from $87,000 (2020) to a peak of $145,000 (2023), then **dipped slightly to $140,000 in 2024** — the first year-over-year decline in the dataset's history.
82. US-only figures show the same pattern: peak $150,000 in 2023, down to $145,450 in 2024 — a **3.7% pullback**, consistent with broader 2024 tech-sector cost discipline reported in industry press.
83. BI & Visualization's share of postings grew from 0% (2020–2021) to 5.8% (2024) — the fastest-growing job category in the dataset by relative share, likely reflecting the maturation of the "citizen analyst" / self-service BI trend.
84. Leadership/Management's share grew steadily from 0% (2020) to 6.2% (2024) — as the field matures, a growing share of the market is management rather than purely technical roles.
85. Data Engineering's postings share peaked in 2022 (30.5%) and has since declined to 18.5% (2024) — this could reflect market saturation, but see the sampling caveat below before treating it as a definitive demand signal.

## 13. Correlation Summary

86. Years of experience vs. total comp: r=0.42 (Levels.fyi, Big Tech population).
87. Years of professional coding vs. converted comp: r=0.14 (Stack Overflow, global developer population) — a materially weaker relationship, most likely because SO respondents span vastly more countries and company tiers where the experience-pay relationship is less standardized.
88. Number of languages known vs. comp: positive but non-monotonic — rises through ~8 languages, then reverses (see §72).

## 14. Methodology Caveats (read before using these numbers in downstream ML/BI work)

89. **Company-size distribution shift is very likely a data-collection artifact, not a market trend.** The primary dataset's Large/Medium/Small split moved from a plausible 45/24/31 (2020) to an implausible 3/97/0 (2024) in a single metric — real markets don't restructure that fast. This most likely reflects a change in how ai-jobs.net classified or sourced respondents over time, not an actual disappearance of large-company data hiring. **Any Power BI visual or ML feature using `company_size` should note this limitation explicitly.**
90. **Experience-level distribution shows a similar suspicious swing** — Senior share jumped from 25.4% (2020) to 71.8% (2023) then fell back to 54.3% (2024). This is more consistent with survey sampling/methodology changes than an actual, real-world seniority shift in the global data workforce.
91. A single dirty row was found in Levels.fyi's `gender` column containing a job title string instead of a gender value — a one-row anomaly, immaterial to aggregate stats, but flagged for a follow-up fix in the Phase 3 cleaning script.
92. Levels.fyi gender comp gap (Female $175,000 vs Male $185,000 median, ~5.4% gap) is reported directionally only — Race/Gender are self-reported optional fields with substantial non-response (31–64%), so this should not be treated as a representative, causal, or complete pay-equity finding.
93. The "Contract" and "Freelance" employment-type figures in `fact_job_postings` are based on very thin samples (26 and 12 rows respectively) — directionally interesting but not statistically reliable.
94. Country-level medians outside the US, UK, and Germany are generally based on samples under 150 rows — treat single-country claims for smaller markets as suggestive, not precise.
95. Cross-source salary comparisons (jobs_fact vs Levels.fyi vs SO) should never be blended into one number — they represent different populations (see Phase 3/4 rationale) and are shown here side-by-side for pattern-spotting only, never combined.

## 15. Business Recommendations (synthesized from the above)

96. **For job seekers:** specializing beyond the generic "Data Scientist" title (e.g., toward Applied Scientist, ML Engineer, or Computer Vision Engineer) correlates with a meaningful pay premium — worth highlighting in the ML-based skill-recommendation engine (Phase 5's downstream ML modules).
97. **For employers competing for talent:** the shrinking remote-work share (54%→24%) suggests remote-friendly employers may currently face less competition for remote-preferring senior candidates than in 2021–2022 — a potential talent-acquisition opportunity worth testing.
98. **For career planners:** the "language breadth sweet spot" (6–8 languages, then diminishing returns) suggests recommending T-shaped skill development — moderate breadth plus real depth — rather than maximizing the raw skill count.
99. **For compensation benchmarking teams:** do not use Big Tech (Levels.fyi) medians as a benchmark for the broader data/analytics labor market — the ~$70,000 gap versus the primary jobs_fact dataset reflects company-tier selection, not the "true" market rate.
100. **For workforce planners tracking BI/self-service analytics growth:** the BI & Visualization category's rapid share growth (0%→5.8%) is worth monitoring as a leading indicator of demand for citizen-analyst tooling and training, independent of headcount in core Data Engineering/Science roles.
101. **For data quality practice generally:** the two suspicious distributional swings (§89, §90) are a reminder that even clean, well-documented public datasets can carry hidden methodology changes — always sanity-check year-over-year categorical shifts before treating them as market signal, not just numerical values.

---

**101 grounded, numbered findings** across salary, roles, geography, companies, skills, education, compensation structure, time trends, correlations, and methodology limitations — every number traceable to the Phase 3 cleaned datasets, with explicit caveats where the data's own artifacts could mislead a careless reader.
