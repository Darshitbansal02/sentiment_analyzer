# api_main.py
import os
import time
import threading
import queue
from typing import Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from zoneinfo import ZoneInfo
import tzlocal

from src.config import Settings
from src.models import analyze_text, get_available_hashtags
from src.data_store import DataStore, Post

# -------------------------
# Global Config & Store
# -------------------------
settings = Settings()
store = DataStore(maxlen=5000)
incoming_q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=10000)

current_hashtag_lock = threading.Lock()
current_hashtag: str = settings.hashtag  # default .env

selected_hashtag_lock = threading.Lock()
selected_hashtag: str | None = None  # dynamic selection

# -------------------------
# Streamer Selection
# -------------------------
from src.streamers.simulate_stream import stream as simulate_stream
try:
    from src.streamers.twitter_stream import TwitterStreamer
except Exception:
    TwitterStreamer = None

def select_streamer(hashtag: str):
    if settings.twitter_bearer_token and TwitterStreamer:
        return "twitter", hashtag
    return "simulate", hashtag

# -------------------------
# Collector Loop
# -------------------------
def collector_loop():
    mode, _ = select_streamer(current_hashtag)
    if mode == "twitter":
        while True:
            with current_hashtag_lock:
                hashtag = current_hashtag
            print(f"[stream] Twitter stream for #{hashtag}")
            ts = TwitterStreamer(settings.twitter_bearer_token, hashtag, incoming_q)
            ts.start()
            while True:
                time.sleep(1)
    else:
        print("[stream] Using simulated stream")
        simulate_stream(incoming_q)

# -------------------------
# Inference Loop
# -------------------------
def inference_loop():
    print("[inference] Warming up model...")
    _ = analyze_text("Model warm up.")
    print("[inference] Ready.")

    while True:
        payload = incoming_q.get()
        try:
            res = analyze_text(payload.get("text", ""))
            post = Post(
                id=str(payload.get("id", time.time())),
                text=payload.get("text", ""),
                timestamp=float(payload.get("timestamp", time.time())),
                source=payload.get("source", "simulate"),
                author=payload.get("author"),
                hashtags=payload.get("hashtags", []),
                label=res["label"],
                confidence=float(res["confidence"]),
                signed=float(res["signed"]),
            )
            store.add(post)
        except Exception as e:
            print("[inference] error:", e)

# -------------------------
# FastAPI App & Lifespan
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=collector_loop, daemon=True).start()
    threading.Thread(target=inference_loop, daemon=True).start()
    yield

app = FastAPI(title="Social Sentiment Analyzer API", lifespan=lifespan)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173", "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# API Models
# -------------------------
class PostOut(BaseModel):
    id: str
    ts: str
    source: str
    author: str | None
    label: str | None
    confidence: float | None
    text: str

# -------------------------
# API Endpoints
# -------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "hashtag": settings.hashtag,
        "source": "twitter" if settings.twitter_bearer_token else "simulate"
    }

@app.get("/api/posts", response_model=List[PostOut])
def get_posts(limit: int = Query(50, ge=1, le=500), hashtag: str | None = Query(None)):
    df = store.recent_window(settings.rolling_window_min)
    if df.empty:
        return []

    if hashtag:
        df = df[df["hashtags"].apply(lambda hs: hashtag.lower() in [h.lower() for h in (hs or [])])]

    df = df.sort_values("ts", ascending=False).head(limit)

    try:
        local_tz = ZoneInfo(tzlocal.get_localzone_name())
    except Exception:
        local_tz = ZoneInfo("UTC")

    return [
        PostOut(
            id=str(r["id"]),
            ts=pd.to_datetime(r["ts"], utc=True).tz_convert(local_tz).isoformat(),
            source=str(r.get("source", "simulate")),
            author=r.get("author"),
            label=r.get("label"),
            confidence=float(r.get("confidence")) if r.get("confidence") is not None else None,
            text=r.get("text", "")
        ) for _, r in df.iterrows()
    ]

@app.get("/api/hashtags", response_model=List[str])
def get_model_hashtags():
    """Return hashtags directly from the model"""
    return sorted(get_available_hashtags())

@app.get("/api/stats/counts")
def stats_counts(minutes: int = Query(5, ge=1, le=60), hashtag: str | None = Query(None)):
    df = store.recent_window(minutes)
    if df.empty:
        return {"positive": 0, "neutral": 0, "negative": 0}

    if hashtag:
        df = df[df["hashtags"].apply(lambda hs: hashtag.lower() in [h.lower() for h in (hs or [])])]

    counts = df["label"].value_counts()
    return {lbl: int(counts.get(lbl, 0)) for lbl in ["positive", "neutral", "negative"]}

@app.get("/api/stats/rolling")
def stats_rolling(minutes: int = Query(5, ge=1, le=120), hashtag: str | None = Query(None)):
    df = store.to_dataframe()
    if df.empty:
        return {"points": []}

    if hashtag:
        df = df[df["hashtags"].apply(lambda hs: hashtag.lower() in [h.lower() for h in (hs or [])])]

    df = df.dropna(subset=["signed"])
    if df.empty:
        return {"points": []}

    try:
        local_tz = ZoneInfo(tzlocal.get_localzone_name())
    except Exception:
        local_tz = ZoneInfo("UTC")

    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert(local_tz)
    rolling_mean = df.set_index("ts").sort_index().rolling(f"{minutes}min")["signed"].mean().dropna()
    return {"points": [{"ts": ts.isoformat(), "value": float(v)} for ts, v in rolling_mean.items()]}

@app.get("/api/hashtags-all", response_model=List[str])
def get_all_hashtags():
    df = store.to_dataframe()
    tags = set(h.lower() for hs_list in df["hashtags"].dropna() for h in hs_list)
    return sorted(tags)

@app.get("/api/_debug/buf-size")
def buf_size():
    return {"buffer": len(store.to_dataframe())}

@app.post("/api/hashtag")
def set_selected_hashtag(payload: dict = Body(...)):
    tag = payload.get("hashtag")
    if tag and isinstance(tag, str):
        with selected_hashtag_lock:
            global selected_hashtag
            selected_hashtag = tag.lower()
        return {"status": "ok", "hashtag": selected_hashtag}
    return {"status": "error", "message": "Invalid hashtag"}

# -------------------------
# Serve Frontend (Optional)
# -------------------------
# FRONT_DIR = Path("frontend/out")
# app.mount("/_next", StaticFiles(directory=FRONT_DIR / "_next"), name="_next")
# if (FRONT_DIR / "static").exists():
#     app.mount("/static", StaticFiles(directory=FRONT_DIR / "static"), name="static")

# @app.get("/", response_class=HTMLResponse)
# async def serve_index():
#     index_file = FRONT_DIR / "index.html"
#     if index_file.exists():
#         return index_file.read_text(encoding="utf-8")
#     return "<h1>Frontend not built yet</h1>"
