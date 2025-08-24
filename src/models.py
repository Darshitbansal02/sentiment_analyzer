from functools import lru_cache
from typing import Dict, Any, List, Union
from transformers import pipeline, AutoTokenizer

DEFAULT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

@lru_cache(maxsize=1)
def get_sentiment_pipeline(model_name: str = DEFAULT_MODEL):
    # Avoid deprecation of return_all_scores by using top_k=None for full distribution.
    tok = AutoTokenizer.from_pretrained(model_name, model_max_length=512, truncation=True)
    nlp = pipeline(
        task="sentiment-analysis",
        model=model_name,
        tokenizer=tok,
        top_k=None,          # full label distribution
        truncation=True,
        max_length=512,
    )
    return nlp

def _to_distribution(outputs: Union[Dict[str, Any], List[Any]]) -> List[Dict[str, Any]]:
    """
    Normalize pipeline outputs into a list[dict(label, score)] representing
    the distribution for a single input, regardless of pipeline return shape.
    Possible shapes:
      - [{'label': 'POSITIVE', 'score': 0.99}]                   # top-1
      - [[{'label': 'NEG', ...}, {'label': 'NEU', ...}, ...]]    # top_k=None (full dist)
      - {'label': 'POSITIVE', 'score': 0.99}                     # rare single-dict form
    """
    if isinstance(outputs, dict):
        return [outputs]

    if isinstance(outputs, list):
        if not outputs:
            return []
        first = outputs[0]
        # Case: full distribution -> [ [ {label,score}... ] ]
        if isinstance(first, list):
            return first
        # Case: top-1 -> [ {label,score} ]
        if isinstance(first, dict):
            return outputs

    raise TypeError(f"Unexpected pipeline output shape: {type(outputs)} -> {outputs!r}")

def analyze_text(text: str) -> Dict[str, Any]:
    nlp = get_sentiment_pipeline()
    raw = nlp(text[:512])  # keep it short for speed
    dist = _to_distribution(raw)  # list of dicts

    # Build a {label: score} dict in lower-case
    scores = {d["label"].lower(): float(d["score"]) for d in dist if "label" in d and "score" in d}

    # Fallback if only top-1 came back
    if not scores and isinstance(raw, dict) and "label" in raw and "score" in raw:
        scores = {raw["label"].lower(): float(raw["score"])}

    # Signed score: pos - neg
    signed = scores.get("positive", 0.0) - scores.get("negative", 0.0)

    # Pick the top label
    label = max(scores, key=scores.get) if scores else "neutral"
    confidence = scores.get(label, 0.0)

    return {
        "label": label,
        "confidence": confidence,
        "scores": scores,
        "signed": signed,
    }
# -----------------------------
# Model-driven hashtags helper
# -----------------------------
def get_available_hashtags() -> list[str]:
    """
    Returns all hashtags that the model can recognize.
    By default, RoBERTa sentiment model only has generic labels: positive, neutral, negative.
    You can extend this list based on your application.
    """
    return ["mycampaign", "sports", "tech", "news"]  # replace/add more as needed

