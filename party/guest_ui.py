"""Guest portal views."""

from __future__ import annotations

import streamlit as st

from party.store import (
    character_by_id,
    find_guest_by_code,
    get_guest_note,
    load_announcements,
    load_event,
    set_guest_note,
)


def _resolve_code() -> str | None:
    params = st.query_params
    raw = params.get("code")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if raw:
        return str(raw).strip()
    return st.session_state.get("guest_code")


def render_guest() -> None:
    st.title("Guest portal")
    event = load_event()
    st.caption(event.get("subtitle") or "Your private party page")

    code = _resolve_code()
    if not code:
        st.markdown("Enter the access code from your host to see event updates and your character card.")
        with st.form("guest_code_form"):
            entered = st.text_input("Access code")
            ok = st.form_submit_button("Enter")
        if ok and entered.strip():
            st.session_state.guest_code = entered.strip().upper()
            st.query_params["code"] = entered.strip().upper()
            st.rerun()
        _public_event_preview(event)
        return

    guest = find_guest_by_code(code)
    if not guest:
        st.error("That access code was not found. Check with the host.")
        if st.button("Try another code"):
            st.session_state.pop("guest_code", None)
            st.query_params.clear()
            st.rerun()
        return

    access_code = guest["access_code"]
    st.session_state.guest_code = access_code
    st.success(f"Welcome, **{guest.get('name')}**.")

    party_tab, character_tab, notes_tab = st.tabs(["Party", "Your character", "My notes"])

    with party_tab:
        _render_party_tab(event)

    with character_tab:
        _render_character_tab(guest)

    with notes_tab:
        _render_notes_tab(access_code)


def _render_party_tab(event: dict) -> None:
    st.markdown(f"## {event.get('title', 'Party')}")
    meta = " · ".join(
        p for p in [event.get("date"), event.get("time"), event.get("location")] if p
    )
    if meta:
        st.markdown(meta)
    if event.get("blurb"):
        st.write(event["blurb"])

    st.markdown("---")
    st.markdown("### Party updates")
    announcements = load_announcements()
    if not announcements:
        st.write("No updates yet. Check back soon.")
    else:
        for item in announcements:
            st.markdown(f"**{item.get('title', 'Update')}**  \n*{item.get('created_at', '')}*")
            st.write(item.get("body", ""))
            st.markdown("---")


def _render_character_tab(guest: dict) -> None:
    pid = guest.get("player_id")
    if not pid:
        st.warning("Your host has not assigned you a character yet. Check back later.")
        return

    char = character_by_id(pid)
    if not char:
        st.error("Character data missing for your assignment. Tell the host.")
        return

    st.markdown(f"### {char.get('title')}")
    st.markdown(f"**Role:** {char.get('role')}")
    accessory = (guest.get("accessory") or char.get("costume_note") or "").strip()
    if accessory:
        st.info(f"**Costume / accessory:** {accessory}")

    if char.get("type") == "suspect":
        if char.get("secret_motive"):
            st.markdown(f"**Secret motive:** {char['secret_motive']}")
        if char.get("alibi"):
            st.markdown(f"**Your alibi:** {char['alibi']}")
        if char.get("may_lie"):
            st.warning("You may LIE if asked direct questions.")
        else:
            st.info(
                "You must tell the truth about what you know "
                "(except keep your motive secret until you choose to share)."
            )
    else:
        if char.get("goal"):
            st.markdown(f"**Your goal:** {char['goal']}")

    st.markdown(f"**Whisper clue to share:** _{char.get('whisper_clue')}_")
    st.caption(
        "Keep this page private — do not show other guests your secret motive "
        "or whether you may lie."
    )


def _render_notes_tab(access_code: str) -> None:
    st.markdown("### My notes")

    widget_key = f"notes_v4_{access_code.strip().upper()}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = get_guest_note(access_code) or ""

    st.text_area(
        "notes_v4",
        height=280,
        key=widget_key,
        label_visibility="collapsed",
        placeholder="",
    )
    if st.button("Save notes", type="primary", key=f"save_{widget_key}"):
        set_guest_note(access_code, st.session_state.get(widget_key, "").strip())
        st.success("Notes saved.")
        st.rerun()


def _public_event_preview(event: dict) -> None:
    with st.expander("Event preview", expanded=True):
        st.markdown(f"**{event.get('title', 'Party')}**")
        meta = " · ".join(
            p for p in [event.get("date"), event.get("time"), event.get("location")] if p
        )
        if meta:
            st.write(meta)
        if event.get("blurb"):
            st.write(event["blurb"])
