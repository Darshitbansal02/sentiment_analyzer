# Social Media Sentiment Analyzer (Hugging Face + Plotly Dash)

A Python project that **streams social posts for a campaign hashtag**, runs **transformer-based sentiment analysis**, and **visualizes rolling statistics** in an interactive **Plotly Dash** dashboard.

- **AI/NLP**: Hugging Face `transformers` pipeline (default: `cardiffnlp/twitter-roberta-base-sentiment-latest`)
- **Dashboard**: Plotly Dash (rolling mean sentiment, counts, and live feed)
- **Streaming**: 
  - Default: **Simulated stream** (no API keys needed)
  - Optional: Twitter (X) **Filtered Stream** via Tweepy if `TWITTER_BEARER_TOKEN` is provided
- **Dev Environment**: Works great in **VS Code**

---

## Quick Start

```bash
# 1) Create and activate virtualenv (Windows PowerShell shown)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) First run with the simulated stream
copy .env.example .env   # Windows
# or: cp .env.example .env   # macOS/Linux

# (Optionally) edit .env to change HASHTAG, refresh rate, etc.
# 4) Launch the app
python app.py
```

Open the dashboard at: http://127.0.0.1:8050/

---

## Enable Twitter/X Streaming (Optional)

1. Create a developer app on X (Twitter) and obtain a **Bearer Token** for API v2 filtered stream.
2. In your `.env` file, set:

```
TWITTER_BEARER_TOKEN=YOUR_TOKEN_HERE
HASHTAG=#YourHashtag
```

3. Re-run:

```bash
python app.py
```

If credentials are valid, the app will switch from the simulated stream to the **live filtered stream** automatically.

> Note: Access to Twitter/X streaming may require elevated/paid access depending on your account and the platform's current policies. The simulated mode always works.

---

## Project Structure

```
sentiment_analyzer/
├─ app.py                 # Entrypoint: starts streamer + dashboard
├─ requirements.txt
├─ .env.example           # Copy to .env and fill values
├─ README.md
├─ src/
│  ├─ models.py           # HF Transformers sentiment pipeline wrapper
│  ├─ data_store.py       # Thread-safe rolling store of posts + sentiments
│  ├─ config.py           # Reads env vars, default settings
│  └─ streamers/
│     ├─ simulate_stream.py  # Simulated posts (works offline)
│     └─ twitter_stream.py   # Tweepy filtered stream client (optional)
├─ scripts/
│  └─ sample_posts.jsonl  # Seed data for simulation
└─ .vscode/
   ├─ launch.json
   └─ settings.json
```

---

## What’s in the Dashboard?

- **Rolling mean sentiment** (window configurable in minutes)
- **Live counts** (Positive / Neutral / Negative) for the recent window
- **Recent posts table** with color-coded sentiment
- Auto-refresh (configurable) without page reload

---

## Customization Ideas

- Swap model in `src/models.py` (e.g., multilingual or domain-specific).
- Add extra sources (Reddit, YouTube comments, Mastodon) as new `streamers/*.py` modules following the same interface.
- Persist to SQLite or a message queue (Kafka, Redis) for scaling.
- Deploy with Docker and a production server (e.g., `waitress` or gunicorn).

---

## Troubleshooting

- **Torch install issues on Windows**: If you have trouble, visit https://pytorch.org/ and follow the recommended install command for your system.
- **Slow first run**: The model downloads on first use; subsequent runs are faster.
- **No data showing**: In simulated mode, ensure `.env` exists and `HASHTAG` is set (default is `#MyCampaign`). In Twitter mode, validate your bearer token and hashtag format (include `#`).

Enjoy building! 🚀
