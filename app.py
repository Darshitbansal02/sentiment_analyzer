import os, time, threading, queue
from typing import Dict, Any

from src.config import Settings
from src.models import analyze_text
from src.data_store import DataStore, Post

# Streamers
from src.streamers.simulate_stream import stream as simulate_stream
try:
    from src.streamers.twitter_stream import TwitterStreamer
except Exception:
    TwitterStreamer = None

# Dash/Plotly
import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output
import plotly.express as px

settings = Settings()
store = DataStore(maxlen=5000)
incoming_q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=10000)

def select_streamer():
    if settings.twitter_bearer_token and TwitterStreamer is not None:
        return ("twitter", settings.hashtag)
    return ("simulate", settings.hashtag)

def collector_loop():
    # Pick source
    mode, hashtag = select_streamer()
    if mode == "twitter":
        print(f"[stream] Using Twitter filtered stream for {hashtag}")
        ts = TwitterStreamer(settings.twitter_bearer_token, hashtag, incoming_q)
        ts.start()
        # Twitter stream runs in internal thread; just idle here
        while True:
            time.sleep(1.0)
    else:
        print(f"[stream] Using simulated stream for {hashtag}")
        simulate_stream(hashtag, incoming_q)

def inference_loop():
    print("[inference] Sentiment model warming up...")
    _ = analyze_text("Model warm up.")
    print("[inference] Ready.")
    while True:
        payload = incoming_q.get()
        try:
            res = analyze_text(payload["text"])
            post = Post(
                id=str(payload.get("id")),
                text=payload.get("text",""),
                timestamp=float(payload.get("timestamp", time.time())),
                source=payload.get("source","simulate"),
                author=payload.get("author"),
                hashtags=payload.get("hashtags", []),
                label=res["label"],
                confidence=float(res["confidence"]),
                signed=float(res["signed"]),
            )
            store.add(post)
        except Exception as e:
            # Keep going on errors
            print("[inference] error:", e)

# Start background threads
threading.Thread(target=collector_loop, daemon=True).start()
threading.Thread(target=inference_loop, daemon=True).start()

# ----------------- Dash App -----------------
app = Dash(__name__)
app.title = "Social Sentiment Analyzer"

app.layout = html.Div([
    html.H2("Social Media Sentiment Analyzer"),
    html.Div(f"Hashtag: {settings.hashtag} | Source: {'Twitter' if settings.twitter_bearer_token else 'Simulated'}"),
    dcc.Interval(id="tick", interval=settings.refresh_ms, n_intervals=0),
    html.Div([
        dcc.Graph(id="rolling-graph"),
        dcc.Graph(id="counts-graph"),
    ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}),
    html.H3("Recent Posts"),
    dash_table.DataTable(
        id="posts-table",
        columns=[
            {"name":"Time","id":"ts","type":"datetime"},
            {"name":"Source","id":"source"},
            {"name":"Author","id":"author"},
            {"name":"Label","id":"label"},
            {"name":"Conf","id":"confidence","type":"numeric","format": {}},
            {"name":"Text","id":"text"},
        ],
        page_size=10,
        style_cell={"whiteSpace":"normal","height":"auto"},
        style_data_conditional=[
            {"if":{"filter_query": "{label} = 'positive'"},"backgroundColor":"#e8f5e9"},
            {"if":{"filter_query": "{label} = 'neutral'"},"backgroundColor":"#eceff1"},
            {"if":{"filter_query": "{label} = 'negative'"},"backgroundColor":"#ffebee"},
        ],
    )
])

@app.callback(
    Output("rolling-graph","figure"),
    Output("counts-graph","figure"),
    Output("posts-table","data"),
    Input("tick","n_intervals"),
)
def refresh(_n):
    df = store.to_dataframe()
    if df.empty:
        fig1 = px.line(title="Rolling Mean Sentiment (empty)")
        fig2 = px.bar(title="Counts (empty)")
        return fig1, fig2, []
    # Rolling mean over configured window (minutes)
    df['value'] = df['signed']
    df = df.dropna(subset=['value'])
    df_roll = df.set_index('ts').sort_index().rolling(f"{settings.rolling_window_min}min")['value'].mean().reset_index()
    fig1 = px.line(df_roll, x="ts", y="value", title=f"Rolling Mean Sentiment ({settings.rolling_window_min} min)")
    # Counts in recent window
    recent = store.recent_window(settings.rolling_window_min)
    counts = recent['label'].value_counts().reindex(['positive','neutral','negative']).fillna(0).astype(int).reset_index()
    counts.columns = ['label','count']
    fig2 = px.bar(counts, x="label", y="count", title=f"Recent Counts ({settings.rolling_window_min} min)")
    # Table: last 50 posts
    table_df = recent.sort_values('ts', ascending=False).head(50)[['ts','source','author','label','confidence','text']]
    return fig1, fig2, table_df.to_dict("records")

if __name__ == "__main__":
    import webbrowser
    host = settings.dash_host
    port = settings.dash_port
    url = f"http://{host}:{port}/"
    print(f"Dashboard running at {url}")
    try:
        # Try to open a browser tab automatically
        webbrowser.open(url)
    except Exception:
        pass
    app.run(host=host, port=port, debug=False)
