# bot

Telegram-driven Instagram automation bot.

Setup
1. Copy `.env.example` to `.env` and fill `TG_BOT_TOKEN` and `OWNER_TG_ID`.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Run

```bash
python try.py
```

Notes
- This tool uses session-based Instagram login or username/password via `instabot`.
- Keep your `.env` secret and do not commit it to version control.