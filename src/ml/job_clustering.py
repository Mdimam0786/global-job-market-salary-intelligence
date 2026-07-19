"""
Phase 8 -- ML Model 4: Job Clustering
Author: Md Imamuddin

Unsupervised segmentation of the primary jobs_fact dataset using KMeans
on encoded categorical features + scaled salary. Elbow method (inertia)
and silhouette score both used to choose k, rather than picking an
arbitrary cluster count.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("job_clustering")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
CAT_FEATURES = ["job_category", "experience_level", "work_setting", "company_size"]
NUM_FEATURES = ["salary_in_usd"]


def main():
    jobs = pd.read_csv(DATA_DIR / "jobs_fact_clean.csv")

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(), CAT_FEATURES),
        ("num", StandardScaler(), NUM_FEATURES),
    ])
    X = preprocessor.fit_transform(jobs[CAT_FEATURES + NUM_FEATURES])

    logger.info("Elbow method + silhouette score across k=3..8")
    inertias, silhouettes = [], []
    for k in range(3, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        inertias.append(km.inertia_)
        # Silhouette on a 5000-row sample -- full-sample silhouette on 14k rows
        # with this many dimensions is slow and the sampled estimate is stable
        sample_idx = np.random.RandomState(42).choice(X.shape[0], size=5000, replace=False)
        sil = silhouette_score(X[sample_idx], labels[sample_idx])
        silhouettes.append(sil)
        logger.info(f"k={k}: inertia={km.inertia_:.0f}, silhouette={sil:.3f}")

    best_k = range(3, 9)[np.argmax(silhouettes)]
    logger.info(f"Best k by silhouette score: {best_k}")

    final_km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    jobs["cluster"] = final_km.fit_predict(X)

    logger.info(f"Cluster profiles (k={best_k}):")
    profile = jobs.groupby("cluster").agg(
        n=("job_id", "count"),
        median_salary=("salary_in_usd", "median"),
        top_category=("job_category", lambda x: x.mode()[0]),
        top_experience=("experience_level", lambda x: x.mode()[0]),
        pct_remote=("work_setting", lambda x: (x == "Remote").mean() * 100),
    )
    logger.info(f"\n{profile.to_string()}")

    jobs[["job_id", "cluster"]].to_csv(Path(__file__).resolve().parents[2] / "data" / "processed" / "job_clusters.csv", index=False)
    profile.to_csv(Path(__file__).resolve().parents[2] / "reports" / "job_cluster_profiles.csv")

    return jobs, profile, best_k


if __name__ == "__main__":
    main()
