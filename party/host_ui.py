"""Host dashboard views."""

from __future__ import annotations

import secrets
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from party.emailer import send_announcement_email, smtp_configured
from party.store import (
    character_by_id,
    generate_access_code,
    guest_emails,
    load_announcements,
    load_characters,
    load_event,
    load_guests,
    load_host_script,
    save_announcements,
    save_event,
    save_guests,
)


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
    """Best-effort public base URL for guest links."""
    try:
        return st.get_option("browser.serverAddress") or "http://localhost:8501"
    except Exception:  # noqa: BLE001
        return "http://localhost:8501"


def guest_link(code: str) -> str:
    # Streamlit query params: guests open the app with ?code=
    return f"?{urlencode({'code': code})}"


def render_host() -> None:
    st.title("Host dashboard")
    st.caption("Lalbagh — manage guests, roles, and party updates.")

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
        f"Player {killer_id} is the secret killer (**{chars.get(killer_id, {}).get('title', 'unknown')}**). "
        "Only you see that here — guests never see who the killer is."
    )

    rows = []
    for g in guests:
        pid = g.get("player_id")
        char = chars.get(pid, {})
        rows.append(
            {
                "name": g.get("name", ""),
                "email": g.get("email", ""),
                "access_code": g.get("access_code", ""),
                "player_id": pid if pid is not None else 0,
                "attending": bool(g.get("attending", True)),
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
            "email": st.column_config.TextColumn("Email"),
            "access_code": st.column_config.TextColumn("Access code", disabled=True),
            "player_id": st.column_config.NumberColumn(
                "Player #", min_value=0, max_value=20, step=1, help="0 = unassigned"
            ),
            "attending": st.column_config.CheckboxColumn("Attending"),
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
                new_guests.append(
                    {
                        "name": name,
                        "email": "" if pd.isna(row["email"]) else str(row["email"]).strip(),
                        "access_code": code,
                        "player_id": pid if pid > 0 else None,
                        "attending": bool(row["attending"]),
                    }
                )
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
        "Share each guest their access code or append it to your Streamlit URL, "
        f"e.g. `http://localhost:8501/?code=CAMP-XXXX`. "
        f"(Configured server address hint: `{_base_url()}`)"
    )
    link_rows = []
    for g in load_guests():
        code = g.get("access_code", "")
        link_rows.append(
            {
                "Name": g.get("name"),
                "Code": code,
                "Link query": guest_link(code) if code else "",
            }
        )
    st.dataframe(pd.DataFrame(link_rows), use_container_width=True, hide_index=True)


def _announcements_tab() -> None:
    st.markdown("### Announcements")
    items = load_announcements()
    event = load_event()

    with st.form("new_announcement"):
        title = st.text_input("Title")
        body = st.text_area("Message", height=140)
        also_email = st.checkbox(
            "Also email guests",
            value=False,
            help="Requires SMTP settings in .env",
        )
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

            if also_email:
                recipients = guest_emails()
                subject = f"[{event.get('title', 'Party')}] {entry['title']}"
                email_body = (
                    f"{entry['body']}\n\n"
                    f"— {event.get('title', 'Party host')}\n"
                    f"{event.get('date', '')} · {event.get('time', '')} · {event.get('location', '')}\n"
                )
                if not smtp_configured():
                    st.warning(
                        "SMTP is not configured. Announcement was saved in-app, but email was skipped. "
                        "Copy `.env.example` to `.env` and fill in SMTP_* values."
                    )
                else:
                    ok, msg = send_announcement_email(
                        subject=subject,
                        body=email_body,
                        recipients=recipients,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
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
        label = f"Player {pid}: {char['title']}"
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
            if char.get("may_lie"):
                st.warning("This player may lie when asked direct questions.")


def _script_tab() -> None:
    st.markdown("### Host cheat sheet & scripts")
    script = load_host_script()
    if script.get("_note"):
        st.caption(script["_note"])

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

    st.markdown("#### Accusation steps")
    for step in script.get("accusation_steps", []):
        st.markdown(f"- {step}")

    killer = character_by_id(load_characters().get("killer_player_id", 8))
    if killer:
        st.error(
            f"Reveal fallback: if the group votes wrong, have **{killer['title']}** confess."
        )
