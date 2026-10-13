"""
Disk-backed embedding cache. Each unique text is embedded once, ever, so
re-running the evaluation or canonicalization costs nothing extra.
"""
import json
import math
import os
from pathlib import Path

CACHE_FILE = Path("data/embedding_cache.json")
MODEL = "text-embedding-3-small"
BATCH = 256

_cache = None
_client = None


def _load():
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    return _cache


def _openai():
    global _client
    if _client is None:
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv()
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def save_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(_load()))


def embed_many(texts):
    """Returns {text: vector}, calling the API only for texts not cached yet."""
    cache = _load()
    missing = sorted({t for t in texts if t and t not in cache})
    for i in range(0, len(missing), BATCH):
        batch = missing[i:i + BATCH]
        resp = _openai().embeddings.create(model=MODEL, input=batch)
        for text, item in zip(batch, resp.data):
            cache[text] = item.embedding
    if missing:
        save_cache()
    return {t: cache[t] for t in texts if t in cache}


def get_embedding(text):
    return embed_many([text]).get(text)


def get_cached_embedding(text, embed_fn=None):
    """Backwards-compatible helper used by ingestion."""
    return get_embedding(text)


def cosine(a, b) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
