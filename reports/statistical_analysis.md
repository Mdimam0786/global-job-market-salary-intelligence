# Phase 7 — Statistical Analysis

**Author:** Md Imamuddin

**Tooling note:** statsmodels wasn't available, so regression uses scikit-learn's `LinearRegression` instead. R², coefficients, and an overall F-test are computed by hand with scipy — same information a statsmodels summary table gives, just put together manually instead of printed as one block. All tests use α = 0.05.

---

## 1. Hypothesis Testing

**H1 — Does remote work pay differently than in-person work?**
Welch's t-test (assumes unequal variances): Remote (n=4,573, mean $145,211) vs. In-person (n=9,413, mean $152,934).
Result: t = -6.94, p < 0.0001 — statistically significant. In-person roles pay more on average here, but the real-world gap is small (about 5%), even though the statistical result is airtight. With over 10,000 rows, even small differences show up as "significant" — that doesn't automatically mean the difference matters much in practice.

**H2 — Does the US pay differently than the UK for data roles?**
US (n=12,465, mean $156,526) vs. UK (n=623, mean $96,287).
Result: t = 25.25, p < 0.000001 — statistically significant, and this time the real-world gap is large too: 62%. Both the statistics and the practical difference agree here.

---

## 2. ANOVA

**Salary by job category:** F = 281.69, p ≈ 0, η² = 0.137 (a medium effect by Cohen's convention). Job category explains about 13.7% of the variation in salary — a real factor, but most of the variation comes from other things (experience, country, company, and factors this dataset doesn't capture at all).

**Salary by experience level:** F = 766.16, p ≈ 0, η² = 0.139 (also a medium effect). This is almost the same effect size as job category. Since experience level and job category explain roughly equal, independent shares of the variation, neither one is just standing in for the other.

---

## 3. Correlation Analysis

| Relationship | r | p | n | Strength |
|---|---|---|---|---|
| Levels.fyi: years of experience → total comp | 0.423 | ≈0 | 62,642 | Moderate |
| Stack Overflow: years coding pro → comp | 0.141 | 8.7e-104 | 23,345 | Weak |

Both correlations are statistically significant given the large sample sizes, but the real-world strength is very different — experience explains about 4x more of the variation in Big Tech pay (Levels.fyi, r²≈0.18) than in the general developer population (Stack Overflow, r²≈0.02). This backs up the earlier EDA finding with a formal test instead of just comparing numbers by eye.

---

## 4. Confidence Intervals (95%, mean salary by experience level)

| Level | Mean | 95% CI | n |
|---|---|---|---|
| Entry-level | $91,872 | [$88,965 – $94,779] | 1,063 |
| Mid-level | $124,097 | [$122,122 – $126,072] | 3,339 |
| Senior | $163,112 | [$161,879 – $164,345] | 9,381 |
| Executive | $192,733 | [$185,982 – $199,483] | 416 |

None of these ranges overlap — good evidence that all four experience levels are genuinely different pay bands, not just random noise around one average. Executive has the widest range, which makes sense since it has the smallest sample (416 rows), but it still doesn't come close to overlapping with Senior.

---

## 5. Regression Analysis

**Model:** salary ~ experience level (ordinal) + job category + work setting + company size

- **R² = 0.250** — the model explains 25% of the variation in salary. That's a reasonable starting point given it only uses 4 basic features and nothing about country, education, or exact job title. It's an honest number, not an inflated one.
- **Overall F-test: F(14, 14184) = 337.6, p ≈ 0** — the model as a whole is statistically significant.
- **Experience level:** each step up (Entry → Mid → Senior → Executive) adds about $29,642, holding everything else constant.
- **Biggest positive effects:** Machine Learning/AI roles (+$53,679), in-person work (+$44,034), remote work (+$37,358) — both remote and in-person beat hybrid here, which lines up with the EDA finding that hybrid's small sample behaves oddly.
- **Biggest negative effects:** small companies (-$43,857), Data Quality/Operations roles (-$23,099) — both make sense, since smaller companies and simpler data roles tend to pay less.

Worth being clear about what this 25% R² means: 75% of salary variation in this market comes from things this simple model doesn't capture — country, specific company, exact title, negotiation, and other factors. The ML models in the next phase add more features and should do better than this baseline, but claiming near-perfect salary prediction from just four basic features would be a red flag in any real review of this work.

---

## 6. Distribution Analysis

| Dataset | Skewness | Excess Kurtosis | Normality (Anderson-Darling) | After log1p |
|---|---|---|---|---|
| `jobs_fact` salary_in_usd | 0.736 (right-skewed) | 0.881 (heavy-tailed) | Not normal (AD=75.99, well above 0.75 critical value) | Skew improves to -0.688 |
| Levels.fyi total comp | 4.512 (strongly right-skewed) | 86.995 (very heavy-tailed) | Not normal (AD=2076, well above 0.75 critical value) | Skew improves to -0.717 |

Neither distribution is normal — both lean right with heavy tails, which is typical for salary data (a long tail of high earners, a floor near zero). Levels.fyi is far more skewed than the primary dataset, which fits with it including senior/staff-level Big Tech pay with large equity components — a handful of very high earners pull the tail hard.

**What this means for the ML phase:** salary and comp targets should be log-transformed before using linear models (tree-based models like XGBoost/LightGBM are much less sensitive to this and can often use the raw numbers directly). Noting this now so it doesn't need to be rediscovered later.

---

## Summary of Statistically Validated Findings

1. In-person pay is a little higher than remote (~5%), and the difference is statistically real but small in practice.
2. The US vs UK pay gap (62%) is both statistically and practically significant.
3. Job category and experience level each independently explain a medium share (~14%) of salary variation.
4. The link between experience and pay is 3x stronger at Big Tech companies than in the general developer population.
5. All four experience levels have non-overlapping confidence intervals — they're genuinely different pay bands.
6. A simple 4-feature regression explains 25% of salary variation — an honest starting point, not an inflated one.
7. Both salary distributions are clearly non-normal and should be log-transformed for linear modeling.
