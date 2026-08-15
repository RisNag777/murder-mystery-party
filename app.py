"""Lalbagh murder mystery party app."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from party.guest_ui import render_guest
from party.host_ui import render_host, require_host_login

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="Lalbagh Murder Mystery",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    st.sidebar.title("Lalbagh Mystery")
    st.sidebar.caption("Murder mystery party")

    # Auto-open guest portal when a code is in the URL
    params = st.query_params
    raw_code = params.get("code")
    if isinstance(raw_code, list):
        raw_code = raw_code[0] if raw_code else None
    default_mode = "Guest portal" if raw_code else "Guest portal"

    mode = st.sidebar.radio(
        "I am a…",
        ["Guest portal", "Host dashboard"],
        index=0 if default_mode == "Guest portal" else 1,
    )

    if mode == "Host dashboard":
        password = os.getenv("HOST_PASSWORD", "")
        if require_host_login(password):
            if st.sidebar.button("Sign out"):
                st.session_state.host_authenticated = False
                st.rerun()
            render_host()
    else:
        render_guest()


if __name__ == "__main__":
    main()
