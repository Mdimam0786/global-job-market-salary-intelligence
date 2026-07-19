"""
Error handling for page render functions.

Streamlit's default behavior on an uncaught exception is a full
stack-trace dump in the app itself -- fine for local development, bad
for a live "showcase" deployment where a visitor hitting one broken
page shouldn't see a Python traceback. @handle_errors wraps a page's
render function, logs the real exception with full traceback to the
log file, and shows a short, friendly message in the app instead.

Author: Md Imamuddin
"""

import functools
import traceback

import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


def handle_errors(page_name: str):
    """Decorator factory -- usage: @handle_errors("Home")"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.error(
                    f"Error rendering page '{page_name}': {exc}\n{traceback.format_exc()}"
                )
                st.error(
                    f"⚠️ Something went wrong loading **{page_name}**. "
                    "This has been logged. Try refreshing, or pick a different "
                    "page from the sidebar."
                )
                with st.expander("Technical details (for debugging)"):
                    st.code(traceback.format_exc(), language="python")
                return None

        return wrapper

    return decorator
