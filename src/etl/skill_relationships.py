"""
Phase 6 -- NLP & Skill Extraction, Part 2: Skill Relationship Analysis
Author: Md Imamuddin

Market-basket-style association analysis over the skill bridge table:
for each pair of skills, compute support, confidence, and lift -- the
same metrics used in retail "customers who bought X also bought Y"
analysis, applied here to "developers who know X also know Y".

Lift > 1 means the two skills co-occur more than chance would predict
(a genuine skill affinity); lift <= 1 means no meaningful relationship
beyond both being common individually.
"""

from pathlib import Path
import sys
from itertools import combinations

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("skill_relationships")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_PATH = DATA_DIR / "skill_association_rules.csv"

MIN_SKILL_SUPPORT = 500   # ignore niche skills with too few respondents to be statistically meaningful
TOP_N_SKILLS = 40         # cap pairwise combinations to the top-N most common skills (compute cost)


def main():
    bridge = pd.read_csv(DATA_DIR / "bridge_respondent_skill.csv",encoding="utf-8-sig")
    dim_skill = pd.read_csv(DATA_DIR / "dim_skill.csv",encoding="utf-8-sig")
    n_respondents = bridge["response_id"].nunique()
    logger.info(f"Bridge rows: {len(bridge)}, respondents: {n_respondents}, skills: {dim_skill.shape[0]}")

    skill_counts = bridge["skill_key"].value_counts()
    top_skills = skill_counts[skill_counts >= MIN_SKILL_SUPPORT].head(TOP_N_SKILLS).index
    logger.info(f"Restricting to top {len(top_skills)} skills with >= {MIN_SKILL_SUPPORT} respondents "
                "(pairwise combinations grow quadratically, and rare skills give unstable lift estimates)")

    bridge_top = bridge[bridge["skill_key"].isin(top_skills)]

    # respondent -> set of skill_keys, restricted to top skills
    resp_skills = bridge_top.groupby("response_id")["skill_key"].apply(set)

    pair_counts = {}
    for skills in resp_skills:
        for a, b in combinations(sorted(skills), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    skill_name_lookup = dim_skill.set_index("skill_key")["skill_name"]
    single_support = skill_counts / n_respondents

    rows = []
    for (a, b), count in pair_counts.items():
        support_ab = count / n_respondents
        support_a = single_support[a]
        support_b = single_support[b]
        confidence_a_to_b = support_ab / support_a
        lift = support_ab / (support_a * support_b)
        rows.append({
            "skill_a": skill_name_lookup[a],
            "skill_b": skill_name_lookup[b],
            "co_occurrence_count": count,
            "support": round(support_ab, 4),
            "confidence_a_to_b": round(confidence_a_to_b, 4),
            "lift": round(lift, 3),
        })

    rules = pd.DataFrame(rows).sort_values("lift", ascending=False)
    rules.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"Wrote {len(rules)} skill pairs to {OUT_PATH}")

    logger.info(f"Top 15 by lift (min 500 co-occurrences):\n"
                f"{rules[rules['co_occurrence_count'] >= 500].head(15).to_string()}")

    return rules


if __name__ == "__main__":
    main()
