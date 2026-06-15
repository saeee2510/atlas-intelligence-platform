import os
import json

CACHE_FILE = "data/embedding_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

def get_cached_embedding(text, embed_fn):
    if text in cache:
        return cache[text]

    emb = embed_fn(text)
    cache[text] = emb

    return emb

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)