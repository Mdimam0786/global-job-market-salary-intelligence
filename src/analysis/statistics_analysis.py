"""
Phase 7 -- Statistics
Author: Md Imamuddin

Note: statsmodels wasn't available, so regression is implemented with
scikit-learn's LinearRegression instead, with R^2, coefficients, and a
manually-computed F-statistic / p-value for overall model significance
(via scipy), so the statistical rigor a statsmodels summary() table would
give is not lost, just assembled by hand.

All tests use alpha = 0.05 unless stated otherwise.
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="scipy")

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("statistics")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def section(title):
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def hypothesis_tests(jobs: pd.DataFrame):
    section("1. HYPOTHESIS TESTING")

    # H1: Remote vs In-person salary -- Welch's t-test (unequal variances assumed)
    remote = jobs.loc[jobs["work_setting"] == "Remote", "salary_in_usd"]
    onsite = jobs.loc[jobs["work_setting"] == "In-person", "salary_in_usd"]
    t_stat, p_val = stats.ttest_ind(remote, onsite, equal_var=False)
    logger.info(f"H1: Remote vs In-person salary (Welch's t-test)")
    logger.info(f"    Remote: n={len(remote)}, mean=${remote.mean():,.0f} | "
                f"In-person: n={len(onsite)}, mean=${onsite.mean():,.0f}")
    logger.info(f"    t={t_stat:.3f}, p={p_val:.4f} -> "
                f"{'REJECT H0 (significant difference)' if p_val < 0.05 else 'FAIL TO REJECT H0 (no significant difference)'}")

    # H2: US vs UK salary
    us = jobs.loc[jobs["company_location"] == "United States", "salary_in_usd"]
    uk = jobs.loc[jobs["company_location"] == "United Kingdom", "salary_in_usd"]
    t_stat2, p_val2 = stats.ttest_ind(us, uk, equal_var=False)
    logger.info(f"H2: US vs UK salary (Welch's t-test)")
    logger.info(f"    US: n={len(us)}, mean=${us.mean():,.0f} | UK: n={len(uk)}, mean=${uk.mean():,.0f}")
    logger.info(f"    t={t_stat2:.3f}, p={p_val2:.6f} -> "
                f"{'REJECT H0' if p_val2 < 0.05 else 'FAIL TO REJECT H0'}")

    return {"remote_vs_onsite": (t_stat, p_val), "us_vs_uk": (t_stat2, p_val2)}


def anova_tests(jobs: pd.DataFrame):
    section("2. ANOVA")

    # One-way ANOVA: salary across job_category
    groups = [g["salary_in_usd"].values for _, g in jobs.groupby("job_category") if len(g) >= 30]
    f_stat, p_val = stats.f_oneway(*groups)

    # Eta-squared effect size (SS_between / SS_total)
    grand_mean = jobs["salary_in_usd"].mean()
    ss_total = ((jobs["salary_in_usd"] - grand_mean) ** 2).sum()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    eta_sq = ss_between / ss_total

    logger.info(f"ANOVA: salary_in_usd ~ job_category (categories with n>=30)")
    logger.info(f"    F={f_stat:.2f}, p={p_val:.2e}, eta-squared={eta_sq:.3f}")
    logger.info(f"    -> {'REJECT H0: job_category explains a significant share of salary variance' if p_val < 0.05 else 'FAIL TO REJECT H0'}")
    logger.info(f"    Effect size interpretation: eta-squared of {eta_sq:.3f} is "
                f"{'small' if eta_sq < 0.06 else 'medium' if eta_sq < 0.14 else 'large'} by Cohen's convention")

    # One-way ANOVA: salary across experience_level
    groups2 = [g["salary_in_usd"].values for _, g in jobs.groupby("experience_level", observed=True)]
    f_stat2, p_val2 = stats.f_oneway(*groups2)
    ss_between2 = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups2)
    eta_sq2 = ss_between2 / ss_total
    logger.info(f"ANOVA: salary_in_usd ~ experience_level")
    logger.info(f"    F={f_stat2:.2f}, p={p_val2:.2e}, eta-squared={eta_sq2:.3f} "
                f"({'large' if eta_sq2 >= 0.14 else 'medium' if eta_sq2 >= 0.06 else 'small'} effect)")

    return {"job_category": (f_stat, p_val, eta_sq), "experience_level": (f_stat2, p_val2, eta_sq2)}


def correlation_analysis(levels: pd.DataFrame, so_salary: pd.DataFrame):
    section("3. CORRELATION ANALYSIS")

    r, p = stats.pearsonr(levels["years_of_experience"], levels["total_yearly_compensation"])
    logger.info(f"Levels.fyi: years_of_experience vs total_yearly_compensation")
    logger.info(f"    Pearson r={r:.3f}, p={p:.2e}, n={len(levels)} -> "
                f"{'statistically significant' if p < 0.05 else 'not significant'} "
                f"({'moderate' if 0.3 <= abs(r) < 0.5 else 'weak' if abs(r) < 0.3 else 'strong'} relationship)")

    def parse_years(x):
        if pd.isna(x):
            return None
        if x == "Less than 1 year":
            return 0.5
        if x == "More than 50 years":
            return 51
        try:
            return float(x)
        except ValueError:
            return None

    so_salary = so_salary.copy()
    so_salary["years_code_pro_num"] = so_salary["YearsCodePro"].apply(parse_years)
    valid = so_salary.dropna(subset=["years_code_pro_num", "ConvertedCompYearly"])
    r2, p2 = stats.pearsonr(valid["years_code_pro_num"], valid["ConvertedCompYearly"])
    logger.info(f"Stack Overflow: YearsCodePro vs ConvertedCompYearly")
    logger.info(f"    Pearson r={r2:.3f}, p={p2:.2e}, n={len(valid)} -> "
                f"{'statistically significant' if p2 < 0.05 else 'not significant'} "
                f"({'moderate' if 0.3 <= abs(r2) < 0.5 else 'weak' if abs(r2) < 0.3 else 'strong'} relationship)")

    return {"levels_exp_comp": (r, p), "so_years_comp": (r2, p2)}


def confidence_intervals(jobs: pd.DataFrame):
    section("4. CONFIDENCE INTERVALS (95%)")

    results = {}
    for level, g in jobs.groupby("experience_level", observed=True):
        mean = g["salary_in_usd"].mean()
        sem = stats.sem(g["salary_in_usd"])
        ci_low, ci_high = stats.t.interval(0.95, len(g) - 1, loc=mean, scale=sem)
        logger.info(f"{level}: mean=${mean:,.0f}, 95% CI=[${ci_low:,.0f}, ${ci_high:,.0f}], n={len(g)}")
        results[level] = (mean, ci_low, ci_high)

    return results


def regression_analysis(jobs: pd.DataFrame):
    section("5. REGRESSION ANALYSIS (scikit-learn, statsmodels unavailable -- see module docstring)")

    df = jobs.copy()
    exp_map = {"Entry-level": 0, "Mid-level": 1, "Senior": 2, "Executive": 3}
    df["exp_ordinal"] = df["experience_level"].map(exp_map)

    cat_cols = ["job_category", "work_setting", "company_size"]
    encoder = OneHotEncoder(drop="first", sparse_output=False)
    encoded = encoder.fit_transform(df[cat_cols].astype(str))
    encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(cat_cols), index=df.index)

    X = pd.concat([df[["exp_ordinal"]], encoded_df], axis=1)
    y = df["salary_in_usd"]

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = model.score(X, y)

    n, k = X.shape
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    f_stat = ((ss_tot - ss_res) / k) / (ss_res / (n - k - 1))
    p_val = 1 - stats.f.cdf(f_stat, k, n - k - 1)

    logger.info(f"Model: salary_in_usd ~ experience_level(ordinal) + job_category + work_setting + company_size")
    logger.info(f"    R-squared = {r2:.3f}  (model explains {r2*100:.1f}% of salary variance)")
    logger.info(f"    Overall F-test: F({k},{n-k-1})={f_stat:.1f}, p={p_val:.2e} -> "
                f"{'model is statistically significant' if p_val < 0.05 else 'model is not significant'}")
    logger.info(f"    Intercept: ${model.intercept_:,.0f}")
    logger.info(f"    Coefficient on experience_level (per level step): ${model.coef_[0]:,.0f}")

    top_coefs = pd.Series(model.coef_[1:], index=X.columns[1:]).sort_values(ascending=False)
    logger.info(f"    Top 5 positive category effects (vs. baseline):\n{top_coefs.head(5)}")
    logger.info(f"    Top 5 negative category effects (vs. baseline):\n{top_coefs.tail(5)}")

    return {"r2": r2, "f_stat": f_stat, "p_val": p_val, "coefficients": top_coefs}


def distribution_analysis(jobs: pd.DataFrame, levels: pd.DataFrame):
    section("6. DISTRIBUTION ANALYSIS")

    for name, series in [("jobs_fact salary_in_usd", jobs["salary_in_usd"]),
                          ("Levels.fyi total_yearly_compensation", levels["total_yearly_compensation"])]:
        skew = stats.skew(series)
        kurt = stats.kurtosis(series)
        # Anderson-Darling instead of Shapiro -- Shapiro is unreliable/capped for n > ~5000
        ad_result = stats.anderson(series, dist="norm")
        logger.info(f"{name}: skewness={skew:.3f} ({'right-skewed' if skew > 0.5 else 'roughly symmetric' if abs(skew) <= 0.5 else 'left-skewed'}), "
                    f"excess kurtosis={kurt:.3f} ({'heavy-tailed' if kurt > 0.5 else 'near-normal tails' if abs(kurt) <= 0.5 else 'light-tailed'})")
        logger.info(f"    Anderson-Darling statistic={ad_result.statistic:.2f} vs. 5% critical value={ad_result.critical_values[2]:.2f} -> "
                    f"{'reject normality' if ad_result.statistic > ad_result.critical_values[2] else 'fail to reject normality'}")

        log_series = np.log1p(series)
        log_skew = stats.skew(log_series)
        logger.info(f"    After log1p transform: skewness={log_skew:.3f} "
                    f"({'much closer to normal' if abs(log_skew) < abs(skew) else 'no improvement'})")


def main():
    jobs = pd.read_csv(DATA_DIR / "jobs_fact_clean.csv")
    levels = pd.read_csv(DATA_DIR / "levels_fyi_clean.csv")
    so_salary = pd.read_csv(DATA_DIR / "so_salary_clean.csv")

    h = hypothesis_tests(jobs)
    a = anova_tests(jobs)
    c = correlation_analysis(levels, so_salary)
    ci = confidence_intervals(jobs)
    reg = regression_analysis(jobs)
    distribution_analysis(jobs, levels)

    return h, a, c, ci, reg


if __name__ == "__main__":
    main()
