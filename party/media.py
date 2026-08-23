"""Shared media helpers for character portraits."""

from __future__ import annotations

import streamlit as st

from party.store import character_image_paths, character_image_urls


def show_character_images(char: dict, *, width: int = 320) -> None:
    """Render portrait image(s) for a character card."""
    urls = character_image_urls(char)
    paths = character_image_paths(char)

    if not urls and not paths:
        st.warning(f"No portrait found for {char.get('title', 'this character')}.")
        return

    # Prefer static URLs (works reliably on Streamlit Cloud).
    sources = urls or [str(p) for p in paths]
    if len(sources) == 1:
        _render_one(sources[0], paths[0] if paths else None, width)
        return

    cols = st.columns(len(sources))
    for col, src, path in zip(cols, sources, paths or [None] * len(sources)):
        with col:
            _render_one(src, path, width)


def _render_one(src: str, path, width: int) -> None:
    # Static URL via HTML is the most reliable on Cloud.
    if src.startswith("./app/static/") or src.startswith("/app/static/"):
        st.markdown(
            f'<img src="{src}" width="{width}" '
            f'style="max-width:100%;height:auto;border-radius:8px;" />',
            unsafe_allow_html=True,
        )
        return
    if path is not None:
        st.image(path.read_bytes(), width=width)
    else:
        st.image(src, width=width)
