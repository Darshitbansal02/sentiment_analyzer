from __future__ import annotations
import time, queue, threading
from typing import Dict, Any
import tweepy

class TwitterStreamer:
    def __init__(self, bearer_token: str, hashtag: str, out_queue: "queue.Queue[Dict[str, Any]]"):
        self.bearer_token = bearer_token
        self.hashtag = hashtag if hashtag.startswith("#") else f"#{hashtag}"
        self.out_queue = out_queue
        self._stream = None
        self._thread = None

    def _start_stream(self):
        hashtag_no_hash = self.hashtag.lstrip("#")
        class Client(tweepy.StreamingClient):
            def on_tweet(self_nonlocal, tweet):
                # Minimal payload
                payload = {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "timestamp": time.time(),
                    "source": "twitter",
                    "author": None,
                    "hashtags": [hashtag_no_hash.lower()],
                }
                try:
                    self.out_queue.put(payload)
                except Exception:
                    pass

            def on_response(self_nonlocal, response):
                return super().on_response(response)

            def on_errors(self_nonlocal, errors):
                return super().on_errors(errors)

            def on_exception(self_nonlocal, exception):
                # Auto-reconnect
                time.sleep(2)
                return

        self._stream = Client(self.bearer_token, wait_on_rate_limit=True)
        # Clear previous rules
        try:
            rules = self._stream.get_rules().data or []
            if rules:
                ids = [r.id for r in rules]
                self._stream.delete_rules(ids)
        except Exception:
            pass
        # Add hashtag rule
        rule_value = f"{self.hashtag} -is:retweet -is:reply"
        self._stream.add_rules(tweepy.StreamRule(value=rule_value, tag="campaign"))
        # Start streaming
        self._stream.filter(expansions=None, tweet_fields=["created_at"], threaded=True)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._start_stream, daemon=True)
        self._thread.start()

    def stop(self):
        try:
            if self._stream:
                self._stream.disconnect()
        except Exception:
            pass
