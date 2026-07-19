"""
Phase 8 -- ML Model 5: Skill Recommendation Engine
Author: Md Imamuddin

Not a trained model in the classifier/regressor sense -- this formalizes
the Phase 6 skill association-rule table into a callable recommender:
given a set of skills someone already knows, recommend the highest-lift
skills they don't yet have, filtered to rules with meaningful support
(avoids recommending a skill that "correlates" with only 3 data points).
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("skill_recommender")

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MIN_CO_OCCURRENCE = 300  # ignore rules backed by too few respondents


class SkillRecommender:
    def __init__(self, rules_path: Path):
        self.rules = pd.read_csv(rules_path)
        self.rules = self.rules[self.rules["co_occurrence_count"] >= MIN_CO_OCCURRENCE]

    def recommend(self, known_skills: list[str], top_n: int = 5) -> pd.DataFrame:
        known_set = set(known_skills)
        candidates = []

        for skill in known_set:
            matches = self.rules[
                (self.rules["skill_a"] == skill) | (self.rules["skill_b"] == skill)
            ].copy()
            matches["recommended_skill"] = matches.apply(
                lambda r: r["skill_b"] if r["skill_a"] == skill else r["skill_a"], axis=1
            )
            candidates.append(matches[["recommended_skill", "lift", "co_occurrence_count"]])

        if not candidates:
            return pd.DataFrame(columns=["recommended_skill", "lift", "co_occurrence_count"])

        combined = pd.concat(candidates)
        combined = combined[~combined["recommended_skill"].isin(known_set)]
        # A skill recommended via multiple known skills gets its best (max lift) score kept
        result = (
            combined.sort_values("lift", ascending=False)
            .drop_duplicates(subset="recommended_skill")
            .head(top_n)
            .reset_index(drop=True)
        )
        return result


def main():
    recommender = SkillRecommender(DATA_DIR / "skill_association_rules.csv")

    examples = [
        ["Python", "SQL"],
        ["React", "JavaScript"],
        ["C#"],
    ]
    for known in examples:
        recs = recommender.recommend(known, top_n=5)
        logger.info(f"Known skills: {known}")
        logger.info(f"Recommended next:\n{recs.to_string(index=False)}\n")

    return recommender


if __name__ == "__main__":
    main()
