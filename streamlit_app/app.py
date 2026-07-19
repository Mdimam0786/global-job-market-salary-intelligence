"""
Main entry point. Run with: streamlit run app.py

Architecture note: this app uses a SINGLE entry point with a
session_state-driven router, not Streamlit's native pages/ directory
auto-navigation. That native feature builds its own sidebar nav UI
automatically from filenames, which is convenient but gives limited
control over grouping, icons, and active-state styling. Since this
spec calls for a fully custom sidebar (sections, icons, dark/light
toggle integrated into the nav), a manual router gives full control at
the cost of writing the router yourself -- a deliberate trade-off, not
an oversight.

Author: Md Imamuddin
"""

import streamlit as st

from config.settings import APP_TITLE, APP_ICON, NAV_SECTIONS, GITHUB_URL, LINKEDIN_URL
from config.theme import inject_theme
from utils.logger import get_logger
from utils.ui_components import render_footer

logger = get_logger(__name__)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# Session state initialization -- guarded so reruns don't reset state
# mid-session (Streamlit reruns this whole script on every interaction;
# without the `not in st.session_state` guard, every click would reset
# the user back to the Home page and light mode).
# ---------------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "theme" not in st.session_state:
    st.session_state.theme = "light"

inject_theme()


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption("Portfolio showcase · Power BI remains the primary BI tool")

    # Theme toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Appearance**")
    with col2:
        is_dark = st.toggle("🌙", value=(st.session_state.theme == "dark"), label_visibility="collapsed")
        new_theme = "dark" if is_dark else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()  # rerun immediately so the new theme's CSS applies
                        # without waiting for the next unrelated interaction

    st.divider()

    # Navigation, grouped by section
    for section in NAV_SECTIONS:
        st.markdown(f'<div class="nav-section-label">{section["section"]}</div>', unsafe_allow_html=True)
        for page in section["pages"]:
            is_active = st.session_state.current_page == page["key"]
            button_type = "primary" if is_active else "secondary"
            if st.button(
                f'{page["icon"]}  {page["label"]}',
                key=f'nav_{page["key"]}',
                use_container_width=True,
                type=button_type,
            ):
                st.session_state.current_page = page["key"]
                st.rerun()

    st.divider()
    st.markdown(
        f"""
        <a href="{GITHUB_URL}" target="_blank" style="text-decoration:none;">🔗 GitHub</a><br>
        <a href="{LINKEDIN_URL}" target="_blank" style="text-decoration:none;">💼 LinkedIn</a>
        <a href="mailto:mdimamuddinf786@gmail.com" style="text-decoration:none;">📧 Email</a>
       
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Page router
# ---------------------------------------------------------------------
# Only "home" is wired up in this first build step -- every other key
# routes to a placeholder so the nav is fully clickable and testable
# right away, without pretending pages exist before they're built.
# Each subsequent page (per your "one at a time" instruction) will
# replace its placeholder branch with a real import + render() call.

page_key = st.session_state.current_page

if page_key == "home":
    from views import home
    home.render()
elif page_key == "eda":
    from views import eda
    eda.render()
elif page_key == "statistics":
    from views import statistics
    statistics.render()
elif page_key == "startup_search":
    from views import job_search
    job_search.render()
elif page_key == "investor_search":
    from views import company_search
    company_search.render()
elif page_key == "country_search":
    from views import country_explorer
    country_explorer.render()
elif page_key == "industry_search":
    from views import skill_explorer
    skill_explorer.render()
elif page_key == "funding_prediction":
    from views import salary_prediction
    salary_prediction.render()
elif page_key == "success_prediction":
    from views import experience_prediction
    experience_prediction.render()
elif page_key == "shap_explain":
    from views import explainability
    explainability.render()
elif page_key == "sql_insights":
    from views import sql_insights
    sql_insights.render()
elif page_key == "architecture":
    from views import architecture
    architecture.render()
elif page_key == "documentation":
    from views import documentation
    documentation.render()
elif page_key == "about":
    from views import about
    about.render()
else:
    st.title(f"🚧 {page_key.replace('_', ' ').title()}")
    st.info(
        "This page hasn't been built yet in this step-by-step build. "
        "It's next in the queue -- see the conversation for the full page order."
    )
    logger.info(f"Visited unbuilt placeholder page: {page_key}")

render_footer()
