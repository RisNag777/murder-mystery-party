"""JSON data load/save helpers for the party app."""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _path(name: str) -> Path:
    return DATA_DIR / name


def load_json(name: str) -> Any:
    with _path(name).open(encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(name: str, data: Any) -> None:
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_event() -> dict:
    return load_json("event.json")


def save_event(event: dict) -> None:
    save_json("event.json", event)


def load_guests() -> list[dict]:
    return load_json("guests.json")


def save_guests(guests: list[dict]) -> None:
    save_json("guests.json", guests)


def load_characters() -> dict:
    return load_json("characters.json")


def load_host_script() -> dict:
    return load_json("host_script.json")


def load_guest_notes() -> dict:
    path = _path("guest_notes.json")
    if not path.exists():
        return {}
    return load_json("guest_notes.json")


def save_guest_notes(notes: dict) -> None:
    save_json("guest_notes.json", notes)


def get_guest_note(access_code: str) -> str:
    notes = load_guest_notes()
    entry = notes.get(access_code.strip().upper(), {})
    if isinstance(entry, str):
        return entry
    return entry.get("text", "")


def set_guest_note(access_code: str, text: str) -> None:
    notes = load_guest_notes()
    notes[access_code.strip().upper()] = {
        "text": text,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_guest_notes(notes)


def character_by_id(player_id: int | None) -> dict | None:
    if player_id is None:
        return None
    deck = load_characters()
    for char in deck.get("characters", []):
        if char.get("player_id") == player_id:
            return char
    return None


def find_guest_by_code(code: str) -> dict | None:
    normalized = code.strip().upper()
    for guest in load_guests():
        if guest.get("access_code", "").strip().upper() == normalized:
            return guest
    return None


def generate_access_code(length: int = 4) -> str:
    """Random guest access code (no fixed prefix)."""
    # Skip ambiguous 0/O/1/I so codes are easier to read aloud.
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
