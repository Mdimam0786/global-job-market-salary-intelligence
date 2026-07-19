"""
Centralized logging for the Streamlit app.

Every module imports get_logger(__name__) rather than configuring its
own handlers -- keeps log format consistent and avoids duplicate
handlers when Streamlit re-executes the script on every interaction
(Streamlit's execution model reruns the whole script top-to-bottom on
every widget interaction, so naive logging setup would otherwise add a
new handler on every single click).

Author: Md Imamuddin
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # Guard against re-adding handlers on every Streamlit script rerun --
    # without this check, the log file would get a fresh duplicate
    # handler (and therefore duplicate log lines) on every user click.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(LOG_DIR / "app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Some hosting platforms (e.g. Streamlit Community Cloud) run a
        # read-only filesystem outside of a temp directory -- fall back
        # to console-only logging rather than crashing the app over it.
        logger.warning("Could not open log file for writing -- console logging only")

    return logger
