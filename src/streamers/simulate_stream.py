import json, time, random, queue, pathlib
from typing import Dict, Any, List
from threading import Lock

# Optional: thread-safe current hashtag if used with your API
current_hashtag_lock = Lock()
current_hashtag: str = "MyCampaign"  # default

def _load_seed() -> List[Dict[str, Any]]:
    seed_path = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "sample_posts.jsonl"
    items = []
    if seed_path.exists():
        with open(seed_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
    return items

# Sentiment templates
POSITIVE_TEXTS = [
    "I love this!", "Absolutely fantastic result", "This is stunning",
    "What a great day", "This rocks!", "Exceeded expectations"
]
NEUTRAL_TEXTS = [
    "Not sure about this", "Meh, it's okay", "Could be better",
    "Just average", "Neutral vibes here", "Fine, nothing special"
]
NEGATIVE_TEXTS = [
    "I hate this", "This is terrible", "So disappointing",
    "Worst experience", "Not happy at all", "Really bad outcome"
]

def stream(out_queue: "queue.Queue[Dict[str, Any]]"):
    seed = _load_seed()
    i = 0
    while True:
        # Fetch current hashtag safely
        with current_hashtag_lock:
            hashtag = current_hashtag

        batch_size = random.randint(1, 3)
        for _ in range(batch_size):
            # Pick sentiment
            sentiment = random.choices(
                ["positive", "neutral", "negative"], weights=[0.4, 0.3, 0.3], k=1
            )[0]

            # Pick text template
            if sentiment == "positive":
                text = random.choice(POSITIVE_TEXTS)
            elif sentiment == "neutral":
                text = random.choice(NEUTRAL_TEXTS)
            else:
                text = random.choice(NEGATIVE_TEXTS)

            # Add variation for realism
            if random.random() < 0.2:
                text += " 😊" if sentiment == "positive" else " 😐" if sentiment == "neutral" else " 😡"

            # Base seed data if available
            base = seed[i % len(seed)] if seed else {}
            i += 1

            payload = {
                "id": f"sim-{int(time.time()*1000)}-{i}",
                "text": f"{text} #{hashtag.strip('#')}",
                "timestamp": time.time(),
                "source": "simulate",
                "author": base.get("author", f"user{random.randint(100,9999)}"),
                "hashtags": [h.lower().lstrip("#") for h in base.get("hashtags",[]) if h] or [hashtag.lower().strip("#")],
                "label": sentiment,
                "confidence": round(random.uniform(0.6, 0.99), 2),
            }
            out_queue.put(payload)

        # Sleep to mimic real streaming
        time.sleep(random.uniform(0.3, 0.8))
