"""
Reusable UI components built on top of the CSS classes injected by
config/theme.py. Views import these instead of hand-writing HTML
strings inline, so a visual tweak happens in one place.

Author: Md Imamuddin
"""

import streamlit as st


def kpi_card(label: str, value: str, gradient: int = 1, delta: str = None):
    """Renders one gradient KPI card. gradient is 1, 2, or 3, matching
    the .kpi-gradient-N classes defined in theme.py."""
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="kpi-card kpi-gradient-{gradient}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_indicator(label: str, status: str = "live"):
    """status: 'live', 'warn', or 'off'."""
    st.markdown(
        f'<span class="status-dot status-{status}"></span>{label}',
        unsafe_allow_html=True,
    )


def skeleton_loader(rows: int = 3):
    """Call this INSTEAD of a spinner while data loads, for a more
    modern "content is coming" feel than Streamlit's default spinner.
    Best used briefly, since st.cache_data means most loads after the
    first are near-instant and a skeleton would just flash unhelpfully --
    reach for this on the first-ever page load or explicitly slow ops."""
    for _ in range(rows):
        st.markdown('<div class="skeleton" style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)


def content_card_open():
    """
    ⚠ Deliberately NOT used to wrap native widgets (charts, tables,
    dataframes). This is a common mistake worth naming directly: an
    st.markdown('<div>...') call renders as its own isolated DOM node --
    any Streamlit widget placed "after" it is a SIBLING element, not a
    CHILD, so the div does not visually enclose it, no matter how it
    looks in the source code order. This function is safe ONLY for
    wrapping pure HTML content you build entirely with st.markdown
    (like kpi_card above). For wrapping real widgets in a bordered/
    shadowed card, use styled_container() below instead, which uses
    Streamlit's native st.container(border=True) -- the actual
    supported mechanism for this as of Streamlit 1.28+.
    """
    st.markdown('<div class="content-card fade-in">', unsafe_allow_html=True)


def content_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def render_footer():
    """
    Shown once, at the very bottom of every page -- called from app.py
    after the page router, not from each individual view, so there's
    one place to update if the author, project name, or stack ever
    changes rather than 14 separate copies.
    """
    from config.settings import APP_TITLE, AUTHOR_NAME, TECH_STACK

    st.divider()
    st.markdown(
        f"""
        <div style="text-align: center; opacity: 0.65; font-size: 0.85rem; padding: 8px 0 4px 0;">
            <strong>{APP_TITLE}</strong> &nbsp;·&nbsp; Developed by {AUTHOR_NAME}<br>
            {" · ".join(TECH_STACK)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def styled_container():
    """
    The CORRECT way to give a group of real widgets (charts, tables,
    metrics) a bordered card look. Returns a native Streamlit container
    context manager -- use it as:

        with styled_container():
            st.plotly_chart(fig)

    This actually encloses its children in the DOM, unlike the HTML
    div pattern above. It uses Streamlit's built-in border styling
    rather than the custom gradient/shadow CSS, which is a real
    trade-off: less visually customized, but actually functions
    correctly for wrapping widgets, which the HTML approach does not.
    """
    return st.container(border=True)
