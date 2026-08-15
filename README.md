# The Lalbagh Glass House Mystery

Streamlit app for hosting a locked-guest murder mystery party: manage roles, post announcements, and share private guest links.

## Setup

```powershell
.\party_env\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set at least `HOST_PASSWORD`. Optionally fill in `SMTP_*` to email announcements.

## Run

```powershell
streamlit run app.py
```

- **Guest portal:** open the app and enter an access code, or use `http://localhost:8501/?code=CAMP-A1B2`
- **Host dashboard:** choose Host in the sidebar and sign in with `HOST_PASSWORD`

## Data

All content lives under `data/` as JSON (no database):

| File | Purpose |
|------|---------|
| `event.json` | Party title, date, location, blurb |
| `guests.json` | Locked guest list, emails, access codes, player assignments |
| `characters.json` | Lalbagh character & clue matrix (20 roles) |
| `announcements.json` | In-app updates feed |
| `host_script.json` | Host cheat sheet and round scripts |

Replace the placeholder story by editing `characters.json` and `host_script.json`.
