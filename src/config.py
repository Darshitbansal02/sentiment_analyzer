import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    hashtag: str = os.getenv("HASHTAG", "#MyCampaign")
    lang_hint: str = os.getenv("LANG_HINT", "en")
    twitter_bearer_token: str | None = os.getenv("TWITTER_BEARER_TOKEN") or None
    dash_host: str = os.getenv("DASH_HOST", "127.0.0.1")
    dash_port: int = int(os.getenv("DASH_PORT", "8050"))
    refresh_ms: int = int(os.getenv("REFRESH_MS", "1500"))
    rolling_window_min: int = int(os.getenv("ROLLING_WINDOW_MIN", "5"))
