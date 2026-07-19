# Machine Learning Report

**Author:** Md Imamuddin

## Tooling Note

XGBoost, LightGBM, and SHAP weren't available during part of development. These substitutes were used instead:
- **Gradient boosting:** scikit-learn's `GradientBoostingRegressor` / `Classifier` — same general approach as XGBoost, slower and with fewer tuning options at scale, but directly comparable results.
- **Feature importance:** scikit-learn's `permutation_importance` instead of SHAP. This shows how much shuffling a feature hurts overall model performance, which is useful but doesn't provide per-prediction explanations or interaction effects the way SHAP does. This is a real gap, not a like-for-like replacement, and is noted here directly.

---

## 1. Salary Prediction

**Features:** job category, employment type, company size, work setting, company location, and experience level, all one-hot encoded. **Target:** salary in USD, log-transformed to correct for its right-skewed distribution (confirmed in the statistical analysis report).

| Model | MAE | RMSE | Test R² | 5-fold CV R² (log scale) |
|---|---|---|---|---|
| Linear Regression | $39,857 | $54,118 | 0.296 | 0.426 ± 0.023 |
| Random Forest | $39,563 | $53,632 | 0.308 | 0.428 ± 0.025 |
| Gradient Boosting (default) | $39,899 | $54,385 | 0.289 | 0.435 ± 0.022 |
| Gradient Boosting (tuned) | $39,542 | — | 0.303 | — |

**Best hyperparameters found** (via RandomizedSearchCV, 15 iterations, 3-fold cross-validation): `n_estimators=200, max_depth=5, learning_rate=0.05, subsample=0.85`.

**Two things worth noting:**
1. All four models land within about 2 points of each other (R² between 0.29 and 0.31). Adding more features — specific job titles, real cost-of-living data, company identity — would likely help more than further tuning of the current feature set.
2. The cross-validation R² (about 0.43) is measured on the log-transformed target, while the test R² (about 0.30) is measured after converting predictions back to real dollars. These two numbers aren't directly comparable — the dollar-scale figure is the one that matters for real-world use, and it's the one reported as the headline result.

**Feature importance (permutation-based):**

| Feature | Importance |
|---|---|
| Company location | 0.296 |
| Job category | 0.207 |
| Experience level | 0.191 |
| Work setting | 0.011 |
| Company size | 0.007 |
| Employment type | ~0.000 |

Company location is the strongest predictor of salary — stronger than job category or experience level on their own. This matches the earlier finding that the US-UK pay gap (62%) was the largest single effect measured anywhere in this project. Employment type barely matters once the other features are known, which makes sense since full-time roles make up 99.6% of the data.

---

## 2. Experience Level Prediction

Job title was deliberately left out as a feature. Many titles literally contain the word "Senior" or "Junior," which would turn this into simple text matching rather than genuine prediction from role and context.

| Model | Test Accuracy | Weighted F1 | 5-fold CV Weighted F1 |
|---|---|---|---|
| Logistic Regression | 0.680 | 0.603 | 0.603 ± 0.010 |
| Random Forest | 0.701 | 0.688 | 0.665 ± 0.010 |

Per-class results:

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Entry-level | 0.48 | 0.40 | 0.44 |
| Executive | 0.49 | 0.25 | 0.33 |
| Mid-level | 0.50 | 0.41 | 0.45 |
| Senior | 0.78 | 0.86 | 0.82 |

Salary turns out to be a strong signal for experience level, which makes intuitive sense since pay generally rises with seniority. Senior is the best-predicted class, since it makes up 66% of the dataset. Executive is the hardest to predict, since it has the smallest sample (83 rows in the test set). The dataset's class imbalance is a real factor here and is reflected honestly in these numbers rather than smoothed over.

**Engineering note:** an earlier version of this model had a bug — a data preprocessing step was missing a setting that caused the salary feature to be silently excluded from training, even though it was intended to be used. This was caught during cross-checking between this analysis and the companion web app, and fixed in `src/ml/classification_models.py`. After the fix, accuracy improved from 67.6% to 70.1%, and the smaller classes (Entry-level, Mid-level) became noticeably easier to predict correctly. The numbers in the tables above already reflect the fix.

---

## 3. Remote Work Status Prediction

| Model | Test Accuracy | Weighted F1 | 5-fold CV Weighted F1 |
|---|---|---|---|
| Logistic Regression | 0.671 | 0.560 | 0.558 ± 0.004 |
| Random Forest | 0.690 | 0.682 | 0.678 ± 0.010 |

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Hybrid | 0.32 | 0.24 | 0.27 |
| In-person | 0.76 | 0.81 | 0.78 |
| Remote | 0.53 | 0.46 | 0.49 |

Same pattern as above: In-person is the best-predicted class (66% of the data), while Hybrid — the smallest class at just 1.5% of rows — is the hardest. The same preprocessing fix mentioned above applies here too, and salary turned out to carry a useful signal for remote-work status as well.

---

## 4. Job Clustering

Used KMeans clustering on job category, experience level, work setting, and company size (one-hot encoded) plus scaled salary. The number of clusters (k) was chosen using silhouette score, tested from k=3 to k=8.

| k | Inertia | Silhouette Score |
|---|---|---|
| 3 | 27,167 | 0.205 |
| 4 | 24,159 | 0.202 |
| 5 | 22,374 | 0.212 |
| 6 | 21,039 | 0.188 |
| 7 | 19,816 | 0.195 |
| **8** | **18,857** | **0.216** |

Silhouette scores stay modest (0.19–0.22) across every value of k tested, meaning the data doesn't split into sharply separated groups — it's more of a gradual, overlapping structure. k=8 scored best, though only by a small margin. This is expected for data made up mostly of categories with a lot of shared structure. Clustering here works well as a descriptive tool for exploring the data, rather than as proof of distinct job types.

One cluster stands out: cluster 3 (1,324 rows), made up mostly of Senior Data Science and Research roles, has the highest median salary of any cluster at $267,720 — worth a closer look in a future update to understand what specifically sets it apart.

---

## 5. Skill Recommendation Engine

Built a simple recommendation tool on top of the skill association data, limited to skill pairs backed by at least 300 respondents to avoid recommending based on too little data.

**Example results:**

| Known skills | Top recommendation | Lift |
|---|---|---|
| Python, SQL | Pip | 1.74 |
| React, JavaScript | Next.js | 2.69 |
| C# | NuGet | 3.40 |

All three examples produce sensible recommendations that match how these tools are actually used together in practice — a good sign that the underlying skill-pairing data generalizes well into a usable recommender.

---

## Model Comparison Summary

| Task | Best Model | Headline Metric | Note |
|---|---|---|---|
| Salary prediction | Random Forest | R² = 0.308 | Feature set has reached its practical limit; location is the dominant factor |
| Experience level prediction | Random Forest | Accuracy = 0.701 | Improved from 0.676 after a preprocessing bug fix; still affected by class imbalance |
| Remote work prediction | Random Forest | Accuracy = 0.690 | Same fix applied; same imbalance pattern |
| Job clustering | k=8 KMeans | Silhouette = 0.216 | Best used as a descriptive tool, not as hard segments |
| Skill recommendation | Association rules | Lift up to 3.4 | Verified against real-world tool pairings |

**Summary:** with this feature set — job category, location, experience level, and related fields — the models explain a meaningful but limited share of the outcome: about 25–31% of salary variation, and 69–70% classification accuracy once the class imbalance is accounted for. A future version of this project would benefit from richer features, such as specific job titles, real company identity, cost-of-living data, and years of experience as an exact number instead of a range.
