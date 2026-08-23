"""Host dashboard views."""

from __future__ import annotations

import secrets
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from party.settings import get_setting
from party.store import (
    character_by_id,
    generate_access_code,
    load_announcements,
    load_characters,
    load_event,
    load_guests,
    load_host_script,
    save_announcements,
    save_event,
    save_guests,
)

DEFAULT_PUBLIC_URL = "https://murder-mystery-party.streamlit.app"


def require_host_login(password: str) -> bool:
    if st.session_state.get("host_authenticated"):
        return True

    st.subheader("Host login")
    with st.form("host_login"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if password and entered == password:
            st.session_state.host_authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    if not password:
        st.warning("Set HOST_PASSWORD in your `.env` file before using the host dashboard.")
    return False


def _base_url() -> str:
    """Public base URL for guest share links."""
    configured = get_setting("PUBLIC_APP_URL", DEFAULT_PUBLIC_URL).strip().rstrip("/")
    return configured or DEFAULT_PUBLIC_URL


def guest_link(code: str) -> str:
    return f"{_base_url()}/?{urlencode({'code': code})}"


def render_host() -> None:
    st.title("Host dashboard")
    st.caption("The Lalbagh Glass House Mystery — manage guests, roles, and party updates.")

    tabs = st.tabs(
        [
            "Event",
            "Guests & roles",
            "Announcements",
            "Character deck",
            "Host script",
        ]
    )

    with tabs[0]:
        _event_tab()
    with tabs[1]:
        _guests_tab()
    with tabs[2]:
        _announcements_tab()
    with tabs[3]:
        _characters_tab()
    with tabs[4]:
        _script_tab()


def _event_tab() -> None:
    st.markdown("### Event details")
    event = load_event()
    with st.form("event_form"):
        title = st.text_input("Title", value=event.get("title", ""))
        subtitle = st.text_input("Subtitle", value=event.get("subtitle", ""))
        date = st.text_input("Date", value=event.get("date", ""))
        time = st.text_input("Time", value=event.get("time", ""))
        location = st.text_input("Location", value=event.get("location", ""))
        blurb = st.text_area("Guest-facing blurb", value=event.get("blurb", ""), height=120)
        if st.form_submit_button("Save event"):
            save_event(
                {
                    "title": title.strip(),
                    "subtitle": subtitle.strip(),
                    "date": date.strip(),
                    "time": time.strip(),
                    "location": location.strip(),
                    "blurb": blurb.strip(),
                }
            )
            st.success("Event details saved.")
            st.rerun()


def _guests_tab() -> None:
    st.markdown("### Guest list & role assignment")
    deck = load_characters()
    killer_id = deck.get("killer_player_id", 8)
    guests = load_guests()
    chars = {c["player_id"]: c for c in deck.get("characters", [])}

    st.info(
        f"**{chars.get(killer_id, {}).get('title', 'Unknown')}** is the secret killer. "
        "Only you see that here — guests never see who the killer is."
    )

    rows = []
    for g in guests:
        pid = g.get("player_id")
        char = chars.get(pid, {})
        rows.append(
            {
                "name": g.get("name", ""),
                "access_code": g.get("access_code", ""),
                "player_id": pid if pid is not None else 0,
                "attending": bool(g.get("attending", True)),
                "accessory": g.get("accessory", "") or "",
                "character": char.get("title", "—"),
                "type": char.get("type", "—"),
                "is_killer": bool(char.get("is_killer")),
            }
        )

    edited = st.data_editor(
        pd.DataFrame(rows),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Name", required=True),
            "access_code": st.column_config.TextColumn("Access code", disabled=True),
            "player_id": st.column_config.NumberColumn(
                "Card #", min_value=0, max_value=20, step=1, help="0 = unassigned; used only for role assignment"
            ),
            "attending": st.column_config.CheckboxColumn("Attending"),
            "accessory": st.column_config.TextColumn("Accessory"),
            "character": st.column_config.TextColumn("Character", disabled=True),
            "type": st.column_config.TextColumn("Type", disabled=True),
            "is_killer": st.column_config.CheckboxColumn("Killer?", disabled=True),
        },
        hide_index=True,
        key="guests_editor",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save guest list", type="primary"):
            new_guests = []
            for _, row in edited.iterrows():
                name = str(row["name"]).strip()
                if not name or name == "nan":
                    continue
                code = str(row["access_code"]).strip()
                if not code or code == "nan":
                    code = generate_access_code()
                pid = int(row["player_id"]) if pd.notna(row["player_id"]) else 0
                accessory = ""
                if "accessory" in row and pd.notna(row["accessory"]):
                    accessory = str(row["accessory"]).strip()
                    if accessory == "nan":
                        accessory = ""
                guest_row = {
                    "name": name,
                    "access_code": code,
                    "player_id": pid if pid > 0 else None,
                    "attending": bool(row["attending"]),
                }
                if accessory:
                    guest_row["accessory"] = accessory
                new_guests.append(guest_row)
            # Validate unique player_ids
            assigned = [g["player_id"] for g in new_guests if g["player_id"]]
            if len(assigned) != len(set(assigned)):
                st.error("Each player_id can only be assigned to one guest.")
            else:
                save_guests(new_guests)
                st.success(f"Saved {len(new_guests)} guests.")
                st.rerun()

    with col2:
        if st.button("Regenerate missing access codes"):
            changed = False
            for g in guests:
                if not g.get("access_code"):
                    g["access_code"] = generate_access_code()
                    changed = True
            if changed:
                save_guests(guests)
                st.success("Generated missing codes.")
                st.rerun()
            else:
                st.info("All guests already have access codes.")

    with col3:
        if st.button("Regenerate ALL access codes"):
            for g in guests:
                g["access_code"] = generate_access_code()
            save_guests(guests)
            st.warning("All access codes regenerated. Re-share guest links.")
            st.rerun()

    st.markdown("#### Guest links")
    st.caption(
        "Share each guest their access code or full link, "
        f"e.g. `{_base_url()}/?code=XXXX`."
    )
    link_rows = []
    for g in load_guests():
        code = g.get("access_code", "")
        link_rows.append(
            {
                "Name": g.get("name"),
                "Code": code,
                "Link": guest_link(code) if code else "",
            }
        )
    st.dataframe(pd.DataFrame(link_rows), use_container_width=True, hide_index=True)


def _announcements_tab() -> None:
    st.markdown("### Announcements")
    items = load_announcements()

    with st.form("new_announcement"):
        title = st.text_input("Title")
        body = st.text_area("Message", height=140)
        submitted = st.form_submit_button("Post announcement", type="primary")

    if submitted:
        if not title.strip() or not body.strip():
            st.error("Title and message are required.")
        else:
            entry = {
                "id": secrets.token_hex(4),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "title": title.strip(),
                "body": body.strip(),
            }
            items = [entry, *items]
            save_announcements(items)
            st.success("Announcement posted in-app.")
            st.rerun()

    st.markdown("#### Feed")
    if not items:
        st.write("No announcements yet.")
    for item in items:
        with st.expander(f"{item.get('title', '(untitled)')} — {item.get('created_at', '')}", expanded=False):
            st.write(item.get("body", ""))
            if st.button("Delete", key=f"del_{item.get('id')}"):
                remaining = [a for a in items if a.get("id") != item.get("id")]
                save_announcements(remaining)
                st.rerun()


def _characters_tab() -> None:
    st.markdown("### Full character deck")
    deck = load_characters()
    if deck.get("_note"):
        st.caption(deck["_note"])
    for rule in deck.get("host_rules", []):
        st.markdown(f"- {rule}")

    guests = {g.get("player_id"): g for g in load_guests() if g.get("player_id")}
    for char in deck.get("characters", []):
        pid = char["player_id"]
        guest = guests.get(pid)
        label = char["title"]
        if char.get("is_killer"):
            label += "  — KILLER"
        if guest:
            label += f"  · assigned to {guest.get('name')}"
        with st.expander(label, expanded=False):
            st.markdown(f"**Role:** {char.get('role')}")
            st.markdown(f"**Type:** {char.get('type')}")
            if char.get("secret_motive"):
                st.markdown(f"**Secret motive:** {char['secret_motive']}")
            if char.get("alibi"):
                st.markdown(f"**Claimed alibi (3:15–3:45 PM):** {char['alibi']}")
            if char.get("goal"):
                st.markdown(f"**Goal:** {char['goal']}")
            st.markdown(f"**Whisper clue:** {char.get('whisper_clue')}")
            if char.get("clue_target"):
                st.markdown(f"**Clue targets:** {char['clue_target']}")
            if char.get("deductive_purpose"):
                st.markdown(f"**Deductive purpose:** {char['deductive_purpose']}")
            if char.get("costume_note"):
                st.markdown(f"**Costume note:** {char['costume_note']}")
            if char.get("may_lie"):
                st.warning("This player may lie when asked direct questions.")


def _script_tab() -> None:
    st.markdown("### Master host packet")
    script = load_host_script()
    if script.get("_note"):
        st.caption(script["_note"])

    overview = script.get("overview") or {}
    if overview:
        st.markdown("#### Event overview")
        for key, label in [
            ("title", "Title"),
            ("date_context", "Date & context"),
            ("location", "Location"),
            ("victim", "Victim"),
            ("crime_scene", "Crime scene"),
            ("murder_weapon", "Murder weapon"),
            ("killer", "Killer"),
            ("motive", "Motive"),
        ]:
            if overview.get(key):
                st.markdown(f"**{label}:** {overview[key]}")

    wraps = script.get("wrist_wrap_red_herrings") or []
    accessories = script.get("accessories") or []
    if accessories:
        st.markdown("#### Guest accessories")
        for item in accessories:
            st.markdown(
                f"- **{item.get('guest')}** ({item.get('character')}) — {item.get('accessory')}"
            )
    if wraps:
        st.markdown("#### Wrist / tattoo red herrings")
        st.caption("Several right-wrist items keep The Tender Coconut Vendor from being singled out on sight alone.")
        for item in wraps:
            st.markdown(f"- **{item.get('character')}** — {item.get('note')}")

    timeline = script.get("timeline") or []
    if timeline:
        st.markdown("#### Timeline & movement map (3:00–3:45 PM)")
        for block in timeline:
            st.markdown(f"**{block.get('time')}**")
            for event in block.get("events", []):
                st.markdown(f"- {event}")

    st.markdown("#### Gameplay flow")
    for round_info in script.get("gameplay_flow", []):
        st.markdown(
            f"**Round {round_info.get('round')}: {round_info.get('name')}** "
            f"({round_info.get('duration')})"
        )
        for step in round_info.get("steps", []):
            st.markdown(f"- {step}")

    st.markdown("#### Setup")
    for step in script.get("setup", []):
        st.markdown(f"- {step}")

    st.markdown("#### Scripts to read aloud")
    for s in script.get("scripts", []):
        with st.expander(s.get("title", f"Script {s.get('id')}"), expanded=s.get("id") == 1):
            st.write(s.get("read_aloud", ""))

    st.markdown("#### Reveal steps")
    for step in script.get("accusation_steps", []):
        st.markdown(f"- {step}")

    killer = character_by_id(load_characters().get("killer_player_id", 8))
    if killer:
        st.error(f"Named killer: **{killer['title']}**.")
