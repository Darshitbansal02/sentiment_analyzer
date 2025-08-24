import threading, time
from collections import deque
from dataclasses import dataclass, asdict
from typing import List, Dict
import pandas as pd

@dataclass
class Post:
    id: str
    text: str
    timestamp: float
    source: str
    author: str | None
    hashtags: List[str]
    label: str | None = None
    confidence: float | None = None
    signed: float | None = None

class DataStore:
    def __init__(self, maxlen: int = 5000):
        self._buf = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, post: Post):
        with self._lock:
            self._buf.append(post)

    def to_dataframe(self) -> pd.DataFrame:
        with self._lock:
            rows = [asdict(p) for p in list(self._buf)]
        if not rows:
            return pd.DataFrame(columns=['id','text','timestamp','source','author','hashtags','label','confidence','signed'])
        df = pd.DataFrame(rows)
        df['ts'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df = df.dropna(subset=['ts']).sort_values('ts')
        return df

    def recent_window(self, minutes: int = 5) -> pd.DataFrame:
        df = self.to_dataframe()
        if df.empty:
            return df
        cutoff = df['ts'].max() - pd.Timedelta(minutes=minutes)
        return df[df['ts'] >= cutoff].copy()
