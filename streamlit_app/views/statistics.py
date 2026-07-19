"""
Statistics page — interactive counterpart to reports/statistical_analysis.md
(Phase 7). Every number here is computed live via scipy against the real
data, not hardcoded from the report -- so it stays correct if the
underlying CSVs are ever updated, and a visitor can pick different
grouping variables rather than only seeing the report's fixed examples.

Author: Md Imamuddin
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

from utils.data_loader import load_jobs, load_levels
from utils.error_handler import handle_errors
from utils.ui_components import kpi_card, styled_container
from config.theme import get_palette


@st.cache_data(ttl=1800)
def _ttest(df: pd.DataFrame, group_col: str, group_a: str, group_b: str, value_col: str):
    a = df.loc[df[group_col] == group_a, value_col].dropna()
    b = df.loc[df[group_col] == group_b, value_col].dropna()
    if len(a) < 2 or len(b) < 2:
        return None
    t_stat, p_val = stats.ttest_ind(a, b, equal_var=False)
    return {
        "t_stat": t_stat, "p_val": p_val,
        "mean_a": a.mean(), "mean_b": b.mean(),
        "n_a": len(a), "n_b": len(b),
    }


@st.cache_data(ttl=1800)
def _anova(df: pd.DataFrame, group_col: str, value_col: str, min_n: int = 30):
    groups = [g[value_col].dropna().values for _, g in df.groupby(group_col) if len(g) >= min_n]
    if len(groups) < 2:
        return None
    f_stat, p_val = stats.f_oneway(*groups)
    grand_mean = df[value_col].mean()
    ss_total = ((df[value_col] - grand_mean) ** 2).sum()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0
    return {"f_stat": f_stat, "p_val": p_val, "eta_sq": eta_sq, "n_groups": len(groups)}


@st.cache_data(ttl=1800)
def _confidence_intervals(df: pd.DataFrame, group_col: str, value_col: str, order: list = None):
    rows = []
    for level, g in df.groupby(group_col, observed=True):
        vals = g[value_col].dropna()
        if len(vals) < 2:
            continue
        mean = vals.mean()
        sem = stats.sem(vals)
        ci_low, ci_high = stats.t.interval(0.95, len(vals) - 1, loc=mean, scale=sem)
        rows.append({"group": level, "mean": mean, "ci_low": ci_low, "ci_high": ci_high, "n": len(vals)})
    result = pd.DataFrame(rows)
    if order:
        result["group"] = pd.Categorical(result["group"], categories=order, ordered=True)
        result = result.sort_values("group")
    return result


@st.cache_data(ttl=1800)
def _distribution_stats(series: pd.Series):
    clean = series.dropna()
    return {
        "skew": stats.skew(clean),
        "kurtosis": stats.kurtosis(clean),
        "mean": clean.mean(),
        "median": clean.median(),
        "std": clean.std(),
    }


@handle_errors("Statistics")
def render():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("📐 Statistics")
    st.caption(
        "Interactive counterpart to `reports/statistical_analysis.md` (Phase 7) — "
        "every result below is computed live via scipy, not copied from the report."
    )

    jobs = load_jobs()
    levels = load_levels()
    if jobs.empty:
        st.warning("No job postings data available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    palette = get_palette()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Hypothesis Testing", "ANOVA", "Correlation", "Confidence Intervals", "Distribution"]
    )

    # ---- Tab 1: Hypothesis Testing ----
    with tab1:
        st.markdown("#### Two-sample t-test (Welch's, unequal variances assumed)")
        col1, col2 = st.columns(2)
        with col1:
            group_col = st.selectbox(
                "Group by", options=["work_setting", "experience_level", "employment_type", "company_size"],
                key="ttest_group_col",
            )
        options = sorted(jobs[group_col].dropna().unique())
        with col2:
            pass
        c1, c2 = st.columns(2)
        with c1:
            group_a = st.selectbox("Group A", options=options, index=0, key="ttest_a")
        with c2:
            default_b_idx = 1 if len(options) > 1 else 0
            group_b = st.selectbox("Group B", options=options, index=default_b_idx, key="ttest_b")

        if group_a == group_b:
            st.info("Pick two different groups to compare.")
        else:
            result = _ttest(jobs, group_col, group_a, group_b, "salary_in_usd")
            if result is None:
                st.warning("Not enough data in one of these groups to run a t-test.")
            else:
                k1, k2, k3 = st.columns(3)
                with k1:
                    kpi_card(f"{group_a} mean", f"${result['mean_a']:,.0f}", gradient=1,
                             delta=f"n={result['n_a']:,}")
                with k2:
                    kpi_card(f"{group_b} mean", f"${result['mean_b']:,.0f}", gradient=2,
                             delta=f"n={result['n_b']:,}")
                with k3:
                    sig = "Significant (p<0.05)" if result["p_val"] < 0.05 else "Not significant"
                    kpi_card("t-statistic", f"{result['t_stat']:.2f}", gradient=3, delta=sig)

                pct_diff = (result["mean_a"] - result["mean_b"]) / result["mean_b"] * 100
                st.markdown(
                    f"**p-value: {result['p_val']:.6f}** — "
                    f"{'statistically significant at α=0.05' if result['p_val'] < 0.05 else 'not statistically significant'}. "
                    f"Practical difference: {pct_diff:+.1f}%."
                )
                if result["p_val"] < 0.05 and abs(pct_diff) < 10:
                    st.info(
                        "⚠️ Statistically significant but practically small — a reminder from "
                        "Phase 7 that large sample sizes can make even minor differences "
                        "'significant' without them being practically important."
                    )

    # ---- Tab 2: ANOVA ----
    with tab2:
        st.markdown("#### One-way ANOVA")
        anova_col = st.selectbox(
            "Grouping variable", options=["job_category", "experience_level", "company_size", "work_setting"],
            key="anova_col",
        )
        anova_result = _anova(jobs, anova_col, "salary_in_usd")
        if anova_result is None:
            st.warning("Not enough groups with sufficient data for ANOVA.")
        else:
            k1, k2, k3 = st.columns(3)
            with k1:
                kpi_card("F-statistic", f"{anova_result['f_stat']:.1f}", gradient=1)
            with k2:
                kpi_card("η² (eta-squared)", f"{anova_result['eta_sq']:.3f}", gradient=2)
            with k3:
                effect = "Small" if anova_result["eta_sq"] < 0.06 else "Medium" if anova_result["eta_sq"] < 0.14 else "Large"
                kpi_card("Effect Size", effect, gradient=3, delta="Cohen's convention")

            st.markdown(
                f"**p-value: {anova_result['p_val']:.2e}** across {anova_result['n_groups']} groups "
                f"(groups with n≥30 only, per Phase 7 methodology)."
            )

            try:
                import plotly.express as px
                fig = px.box(
                    jobs, x=anova_col, y="salary_in_usd",
                    labels={anova_col: "", "salary_in_usd": "Salary (USD)"},
                    color_discrete_sequence=[palette["accent"]],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10), height=420,
                )
                with styled_container():
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.info("Install `plotly` to see the box plot here.")

    # ---- Tab 3: Correlation ----
    with tab3:
        st.markdown("#### Correlation: experience vs. total compensation (Levels.fyi)")
        if levels.empty:
            st.warning("Levels.fyi data not available.")
        else:
            r, p = stats.pearsonr(levels["years_of_experience"], levels["total_yearly_compensation"])
            k1, k2, k3 = st.columns(3)
            with k1:
                kpi_card("Pearson r", f"{r:.3f}", gradient=1)
            with k2:
                kpi_card("r²", f"{r**2:.3f}", gradient=2, delta="variance explained")
            with k3:
                strength = "Weak" if abs(r) < 0.3 else "Moderate" if abs(r) < 0.5 else "Strong"
                kpi_card("Strength", strength, gradient=3, delta=f"p={p:.2e}")

            try:
                import plotly.express as px
                sample = levels.sample(min(5000, len(levels)), random_state=42)  # sample for render speed
                fig = px.scatter(
                    sample, x="years_of_experience", y="total_yearly_compensation",
                    trendline="ols", opacity=0.3,
                    labels={"years_of_experience": "Years of Experience", "total_yearly_compensation": "Total Comp (USD)"},
                    color_discrete_sequence=[palette["accent"]],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10), height=420,
                )
                with styled_container():
                    st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    "Scatter shows a random sample of 5,000 points for rendering speed — "
                    "the correlation statistic above is computed on the full dataset."
                )
            except ImportError:
                st.info("Install `plotly` (with `statsmodels` for the trendline) to see this chart.")

    # ---- Tab 4: Confidence Intervals ----
    with tab4:
        st.markdown("#### 95% confidence intervals by experience level")
        exp_order = ["Entry-level", "Mid-level", "Senior", "Executive"]
        ci_df = _confidence_intervals(jobs, "experience_level", "salary_in_usd", order=exp_order)

        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=ci_df["group"].astype(str), y=ci_df["mean"],
                error_y=dict(
                    type="data",
                    array=ci_df["ci_high"] - ci_df["mean"],
                    arrayminus=ci_df["mean"] - ci_df["ci_low"],
                ),
                marker_color=palette["accent"],
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=420,
                yaxis_title="Mean Salary (USD)",
            )
            with styled_container():
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install `plotly` to see this chart.")

        st.dataframe(
            ci_df.rename(columns={
                "group": "Experience Level", "mean": "Mean", "ci_low": "95% CI Lower",
                "ci_high": "95% CI Upper", "n": "n",
            }).style.format({"Mean": "${:,.0f}", "95% CI Lower": "${:,.0f}", "95% CI Upper": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "None of these intervals overlap — strong evidence all four experience tiers "
            "are genuinely distinct pay bands, not noise around a shared mean (see Phase 7)."
        )

    # ---- Tab 5: Distribution Analysis ----
    with tab5:
        st.markdown("#### Salary distribution shape")
        log_transform = st.toggle("Apply log1p transform", value=False)

        values = np.log1p(jobs["salary_in_usd"]) if log_transform else jobs["salary_in_usd"]
        dist_stats = _distribution_stats(values)

        k1, k2, k3 = st.columns(3)
        with k1:
            skew_label = "Right-skewed" if dist_stats["skew"] > 0.5 else "Roughly symmetric" if abs(dist_stats["skew"]) <= 0.5 else "Left-skewed"
            kpi_card("Skewness", f"{dist_stats['skew']:.3f}", gradient=1, delta=skew_label)
        with k2:
            kurt_label = "Heavy-tailed" if dist_stats["kurtosis"] > 0.5 else "Near-normal tails"
            kpi_card("Excess Kurtosis", f"{dist_stats['kurtosis']:.3f}", gradient=2, delta=kurt_label)
        with k3:
            kpi_card("Median", f"${dist_stats['median']:,.0f}" if not log_transform else f"{dist_stats['median']:.2f}", gradient=3)

        try:
            import plotly.express as px
            fig = px.histogram(
                values, nbins=60,
                labels={"value": "log1p(Salary)" if log_transform else "Salary (USD)"},
                color_discrete_sequence=[palette["accent_2"]],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=380, showlegend=False,
            )
            with styled_container():
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install `plotly` to see the histogram.")

        st.caption(
            "Toggle the log transform to see the Phase 7 finding directly: salary is "
            "significantly right-skewed and heavy-tailed in raw form, and log1p brings "
            "skewness much closer to symmetric — relevant for any linear model trained on this target."
        )

    st.markdown("</div>", unsafe_allow_html=True)
