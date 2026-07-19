"""
App-wide settings and constants. Import from here rather than
hardcoding paths/strings in individual views, so a deployment-path
change is a one-line edit, not a find-and-replace across the app.

Author: Md Imamuddin
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # streamlit_app/ -- assets, .streamlit, etc. live here
REPO_ROOT = BASE_DIR.parent  # repo root -- shared data/, reports/, sql/, docs/ live here
DATA_DIR = REPO_ROOT / "data" / "processed"

APP_TITLE = "Global Job Market & Salary Intelligence"
APP_ICON = "📊"
AUTHOR_NAME = "Md Imamuddin"
# Matches the tech stack line in README.md -- kept here too since the
# footer needs it on every page, not just the README.
TECH_STACK = ["Python", "pandas", "scikit-learn", "PostgreSQL", "Power BI", "Streamlit"]

# Data file names -- centralized so a rename only needs updating here
FILES = {
    "jobs": "jobs_fact_clean.csv",
    "levels": "levels_fyi_clean.csv",
    "so_salary": "so_salary_clean.csv",
    "so_skills": "so_skills_clean.csv",
    "dim_skill": "dim_skill.csv",
    "skill_bridge": "bridge_respondent_skill.csv",
    "skill_rules": "skill_association_rules.csv",
    "job_clusters": "job_clusters.csv",
}

# These live in the repo root's reports/ folder, not data/processed/ --
# kept as a separate dict since they're ML outputs, not source data
REPORT_FILES = {
    "model_comparison": "salary_model_comparison.csv",
    "feature_importance": "salary_feature_importance.csv",
}
REPORTS_DIR = REPO_ROOT / "reports"

# External links -- placeholders, replace with your actual URLs before deploying
GITHUB_URL = "https://github.com/Mdimam0786"
LINKEDIN_URL = "https://www.linkedin.com/in/md-imamuddin-5457391a9/"
RESUME_PATH = BASE_DIR / "assets" / "resume.pdf"

# Ordered nav structure -- single source of truth for the sidebar.
# icon values are Streamlit's built-in Material-style icon names
# (used with st.page_link / st.button(icon=...) in newer Streamlit).
NAV_SECTIONS = [
    {
        "section": "Overview",
        "pages": [
            {"key": "home", "label": "Home", "icon": "🏠"},
            {"key": "eda", "label": "EDA Explorer", "icon": "🔍"},
            {"key": "statistics", "label": "Statistics", "icon": "📐"},
        ],
    },
    {
        "section": "Search",
        "pages": [
            {"key": "startup_search", "label": "Job Postings Search", "icon": "🔎"},
            {"key": "investor_search", "label": "Company Search", "icon": "🏢"},
            {"key": "country_search", "label": "Country Explorer", "icon": "🌍"},
            {"key": "industry_search", "label": "Skill / Category Explorer", "icon": "🧩"},
        ],
    },
    {
        "section": "Machine Learning",
        "pages": [
            {"key": "funding_prediction", "label": "Salary Prediction", "icon": "💰"},
            {"key": "success_prediction", "label": "Experience-Level Prediction", "icon": "🎯"},
            {"key": "shap_explain", "label": "Model Explainability", "icon": "🧠"},
        ],
    },
    {
        "section": "Insights",
        "pages": [
            {"key": "sql_insights", "label": "SQL Insights", "icon": "🗄️"},
            {"key": "architecture", "label": "Project Architecture", "icon": "🏗️"},
        ],
    },
    {
        "section": "About",
        "pages": [
            {"key": "documentation", "label": "Documentation", "icon": "📚"},
            {"key": "about", "label": "About / Contact", "icon": "👤"},
        ],
    },
]
