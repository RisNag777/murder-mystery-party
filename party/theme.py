"""Visual theme helpers for the Lalbagh Glass House Mystery app."""

from __future__ import annotations

import streamlit as st

# Served via Streamlit static file serving (see .streamlit/config.toml)
BACKGROUND_URL = "./app/static/lalbagh-glass-house.png"


def apply_background() -> None:
    """Put the Glass House photo on the main content card only (not the page chrome)."""
    st.markdown(
        f"""
        <style>
        /* Keep page chrome plain — no full-app background image */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {{
            background-image: none !important;
            background-color: #e6ebe3 !important;
        }}

        [data-testid="stHeader"] {{
            background: rgba(230, 235, 227, 0.85) !important;
        }}

        /* The content card that holds "Guest portal" / host dashboard */
        [data-testid="stMainBlockContainer"],
        section.main .block-container {{
            background-color: transparent !important;
            background-image:
                linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.58) 0%,
                    rgba(255, 255, 255, 0.78) 100%
                ),
                url("{BACKGROUND_URL}") !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: local !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
