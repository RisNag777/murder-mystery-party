# The Lalbagh Glass House Mystery

Streamlit app for hosting a locked-guest murder mystery party: manage roles, post announcements, and share private guest links.

**Live app:** [https://murder-mystery-party.streamlit.app/](https://murder-mystery-party.streamlit.app/)

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

- **Guest portal:** open the app and enter an access code, or use `https://murder-mystery-party.streamlit.app/?code=XXXX`
- **Host dashboard:** choose Host in the sidebar and sign in with `HOST_PASSWORD`

## Deploy to Streamlit Community Cloud

App is deployed at [https://murder-mystery-party.streamlit.app/](https://murder-mystery-party.streamlit.app/).

To redeploy or recreate:

1. Push this repo to GitHub (`https://github.com/RisNag777/murder-mystery-party`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. **New app** / manage existing app:
   - **Repository:** `RisNag777/murder-mystery-party`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Under **Advanced settings → Secrets**, set:

```toml
HOST_PASSWORD = "your-real-host-password"
PUBLIC_APP_URL = "https://murder-mystery-party.streamlit.app"
```

Guests open the live URL (optionally with `?code=THEIR-CODE`). Host signs in from the sidebar with `HOST_PASSWORD`.

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
