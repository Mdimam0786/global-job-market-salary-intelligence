"""
Phase 6 -- NLP & Skill Extraction, Part 1: Skill Bridge Table Builder
Author: Md Imamuddin

Unpivots Stack Overflow's five semicolon-delimited multi-select columns
(LanguageHaveWorkedWith, DatabaseHaveWorkedWith, PlatformHaveWorkedWith,
WebframeHaveWorkedWith, ToolsTechHaveWorkedWith) into the dim_skill /
bridge_respondent_skill tables designed in Phase 4.

This is the real "NLP-adjacent" data engineering step for this project:
there are no free-text job descriptions in any of our three sources (see
Phase 2 honesty audit -- flagged as unavailable rather than fabricated),
so "skill extraction" here means structured multi-select parsing rather
than named-entity recognition over prose. That's an honest description
of what the data supports, not a workaround to hide.
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.logger import get_logger

logger = get_logger("build_skill_bridge")

IN_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "so_skills_clean.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

SKILL_COLUMNS = {
    "LanguageHaveWorkedWith": "Language",
    "DatabaseHaveWorkedWith": "Database",
    "PlatformHaveWorkedWith": "Platform",
    "WebframeHaveWorkedWith": "Webframe",
    "ToolsTechHaveWorkedWith": "Tool",
}


def build_dim_skill(df: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct (skill_name, skill_category) pair."""
    rows = []
    for col, category in SKILL_COLUMNS.items():
        skills = df[col].dropna().str.split(";").explode().str.strip().unique()
        for s in skills:
            if s:  # guard against empty strings from trailing semicolons
                rows.append({"skill_name": s, "skill_category": category})
    dim_skill = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    dim_skill.insert(0, "skill_key", range(1, len(dim_skill) + 1))
    return dim_skill


def build_bridge(df: pd.DataFrame, dim_skill: pd.DataFrame) -> pd.DataFrame:
    """One row per (response_id, skill_key) pair."""
    skill_lookup = dim_skill.set_index(["skill_name", "skill_category"])["skill_key"]

    bridge_rows = []
    for col, category in SKILL_COLUMNS.items():
        sub = df[["ResponseId", col]].dropna(subset=[col]).copy()
        sub[col] = sub[col].str.split(";")
        sub = sub.explode(col)
        sub[col] = sub[col].str.strip()
        sub = sub[sub[col] != ""]
        sub["skill_key"] = sub[col].map(lambda s: skill_lookup.get((s, category)))
        bridge_rows.append(sub[["ResponseId", "skill_key"]].rename(columns={"ResponseId": "response_id"}))

    bridge = pd.concat(bridge_rows, ignore_index=True).dropna(subset=["skill_key"])
    bridge["skill_key"] = bridge["skill_key"].astype(int)
    bridge = bridge.drop_duplicates()
    bridge.insert(0, "bridge_id", range(1, len(bridge) + 1))
    return bridge


def main():
    logger.info(f"Loading: {IN_PATH}")
    df = pd.read_csv(IN_PATH,encoding="utf-8-sig")
    logger.info(f"Loaded shape: {df.shape}")

    dim_skill = build_dim_skill(df)
    logger.info(f"Built dim_skill: {dim_skill.shape[0]} distinct skills across "
                f"{dim_skill['skill_category'].nunique()} categories")
    logger.info(f"Skills per category:\n{dim_skill['skill_category'].value_counts()}")

    bridge = build_bridge(df, dim_skill)
    logger.info(f"Built bridge_respondent_skill: {len(bridge)} (respondent, skill) pairs "
                f"across {bridge['response_id'].nunique()} respondents")

    dim_skill.to_csv(OUT_DIR / "dim_skill.csv", index=False,encoding="utf-8-sig")
    bridge.to_csv(OUT_DIR / "bridge_respondent_skill.csv", index=False,encoding="utf-8-sig")
    logger.info(f"Wrote {OUT_DIR / 'dim_skill.csv'} and {OUT_DIR / 'bridge_respondent_skill.csv'}")

    return dim_skill, bridge


if __name__ == "__main__":
    main()
