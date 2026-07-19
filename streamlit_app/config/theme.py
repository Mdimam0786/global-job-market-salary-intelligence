"""
Theme system.

Honest technical note: Streamlit's [theme] section in .streamlit/config.toml
sets the app's theme ONCE at server start and can't be flipped at runtime
by user action -- there's no supported API to swap primaryColor/
backgroundColor mid-session the way a real dark-mode toggle needs.
The workaround every production Streamlit app uses (and the one here)
is CSS injection: config.toml sets a light-mode baseline, and this
module injects a <style> block that overrides colors via CSS variables
based on st.session_state.theme. This is a well-established pattern,
not a hack -- but it's worth understanding why it's two layers instead
of one config setting.

Author: Md Imamuddin
"""

import streamlit as st

LIGHT = {
    "bg": "#FFFFFF",
    "bg_secondary": "#F5F6F8",
    "card_bg": "#FFFFFF",
    "text": "#1A1A1A",
    "text_secondary": "#5B5B5B",
    "border": "#E5E7EB",
    "accent": "#2A78D6",
    "accent_2": "#1BAF7A",
    "gradient_1": "linear-gradient(135deg, #2A78D6 0%, #1BAF7A 100%)",
    "gradient_2": "linear-gradient(135deg, #4A3AA7 0%, #2A78D6 100%)",
    "gradient_3": "linear-gradient(135deg, #EDA100 0%, #EB6834 100%)",
    "shadow": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    "shadow_hover": "0 8px 24px rgba(0,0,0,0.10)",
}

DARK = {
    "bg": "#0E1117",
    "bg_secondary": "#161B22",
    "card_bg": "#1A1F29",
    "text": "#E6E6E6",
    "text_secondary": "#9CA3AF",
    "border": "#2D3340",
    "accent": "#4B94E8",
    "accent_2": "#2ECC91",
    "gradient_1": "linear-gradient(135deg, #2A5FA8 0%, #17875E 100%)",
    "gradient_2": "linear-gradient(135deg, #3B2E85 0%, #2A5FA8 100%)",
    "gradient_3": "linear-gradient(135deg, #B87D00 0%, #B84F1F 100%)",
    "shadow": "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
    "shadow_hover": "0 8px 24px rgba(0,0,0,0.5)",
}


def inject_theme():
    """Call once near the top of app.py, after st.session_state.theme
    is guaranteed to exist."""
    palette = DARK if st.session_state.get("theme") == "dark" else LIGHT

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background-color: {palette["bg"]};
            color: {palette["text"]};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {palette["bg_secondary"]};
            border-right: 1px solid {palette["border"]};
        }}

        /* ---- KPI Card ---- */
        .kpi-card {{
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            color: white;
            box-shadow: {palette["shadow"]};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            cursor: default;
        }}
        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: {palette["shadow_hover"]};
        }}
        .kpi-card .kpi-label {{
            font-size: 0.8rem;
            font-weight: 500;
            opacity: 0.9;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .kpi-card .kpi-value {{
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.1;
        }}
        .kpi-card .kpi-delta {{
            font-size: 0.78rem;
            opacity: 0.85;
            margin-top: 0.35rem;
        }}
        .kpi-gradient-1 {{ background: {palette["gradient_1"]}; }}
        .kpi-gradient-2 {{ background: {palette["gradient_2"]}; }}
        .kpi-gradient-3 {{ background: {palette["gradient_3"]}; }}

        /* ---- Generic content card ---- */
        .content-card {{
            background-color: {palette["card_bg"]};
            border: 1px solid {palette["border"]};
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            box-shadow: {palette["shadow"]};
            transition: box-shadow 0.2s ease;
        }}
        .content-card:hover {{
            box-shadow: {palette["shadow_hover"]};
        }}

        /* ---- Status indicator dot ---- */
        .status-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }}
        .status-live {{ background-color: {palette["accent_2"]}; box-shadow: 0 0 6px {palette["accent_2"]}; }}
        .status-warn {{ background-color: #EDA100; }}
        .status-off {{ background-color: #9CA3AF; }}

        /* ---- Nav button (used inside the custom sidebar) ---- */
        .nav-section-label {{
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: {palette["text_secondary"]};
            margin: 1rem 0 0.35rem 0.25rem;
        }}
        div[data-testid="stSidebar"] button {{
            transition: background-color 0.15s ease, transform 0.1s ease;
            border-radius: 10px !important;
        }}
        div[data-testid="stSidebar"] button:hover {{
            transform: translateX(2px);
        }}

        /* ---- Loading skeleton ---- */
        .skeleton {{
            background: linear-gradient(90deg, {palette["border"]} 25%, {palette["bg_secondary"]} 50%, {palette["border"]} 75%);
            background-size: 200% 100%;
            animation: skeleton-loading 1.4s ease-in-out infinite;
            border-radius: 10px;
            height: 1.2rem;
        }}
        @keyframes skeleton-loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        /* ---- Fade-in animation for page content ---- */
        .fade-in {{
            animation: fadeIn 0.4s ease-in;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        h1, h2, h3 {{ font-weight: 700; letter-spacing: -0.01em; }}

        /* Hide Streamlit's default hamburger menu + "Made with Streamlit"
           footer for a cleaner, more "product" feel -- standard practice
           for a portfolio/showcase deployment, not something hiding errors */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_palette() -> dict:
    """Lets a view (e.g. for a Plotly chart's colorway) fetch the
    current theme's colors without duplicating the LIGHT/DARK dicts."""
    return DARK if st.session_state.get("theme") == "dark" else LIGHT
