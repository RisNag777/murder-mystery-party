# The Lalbagh Glass House Mystery

Streamlit app for hosting a locked-guest murder mystery party: manage roles, post announcements, and share private guest links.

## Setup

```powershell
.\party_env\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set at least `HOST_PASSWORD`.

## Run locally

```powershell
streamlit run app.py
```

- **Guest portal:** open the app and enter an access code, or use `http://localhost:8501/?code=CAMP-A1B2`
- **Host dashboard:** choose Host in the sidebar and sign in with `HOST_PASSWORD`

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (already at `https://github.com/RisNag777/murder-mystery-party`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** and choose:
   - **Repository:** `RisNag777/murder-mystery-party`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Under **Advanced settings → Secrets**, paste:

```toml
HOST_PASSWORD = "your-real-host-password"
```

5. Click **Deploy**. Your public URL will look like `https://murder-mystery-party-….streamlit.app`.

Guests can open that URL (optionally with `?code=THEIR-CODE`). Host signs in from the sidebar with `HOST_PASSWORD`.

**Note:** Guest notes and host edits to JSON files on Cloud are ephemeral (reset when the app reboots). For the party, keep important guest/role data in the repo’s `data/` files.

## Data

All content lives under `data/` as JSON (no database):

| File | Purpose |
|------|---------|
| `event.json` | Party title, date, location, blurb |
| `guests.json` | Locked guest list, access codes, player assignments |
| `characters.json` | Lalbagh character & clue matrix (20 roles) |
| `announcements.json` | In-app updates feed |
| `host_script.json` | Host cheat sheet and round scripts |

Background image: `assets/lalbagh-glass-house.png` (also served from `static/`)

Replace the story by editing `characters.json` and `host_script.json`.
