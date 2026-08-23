"""Read settings from Streamlit secrets (Cloud) or environment (.env locally)."""

from __future__ import annotations

import os


def get_setting(key: str, default: str = "") -> str:
    try:
        import streamlit as st

        if key in st.secrets:
            value = st.secrets[key]
            return default if value is None else str(value)
    except Exception:  # noqa: BLE001 — secrets unavailable outside Streamlit / before init
        pass
    return os.getenv(key, default)
