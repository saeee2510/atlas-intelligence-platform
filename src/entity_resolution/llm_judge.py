"""
LLM judge for pairs the scoring model is unsure about.

Decisions are cached on disk by (prompt version, model, pair), so evaluation
runs are reproducible and repeated runs cost nothing.
"""
import hashlib
import json
import os
import time
from pathlib import Path

MODEL = "gpt-4o-mini"
PROMPT_VERSION = "v2"
CACHE_FILE = Path("data/llm_judgments.json")

PROMPT = """Decide whether two company records refer to the SAME legal entity.

Rules:
- Name variants, legal suffixes, typos, abbreviations, and stock tickers of the
  same company ARE the same entity (e.g. "IBM" and "International Business Machines").
- A company that was renamed IS the same entity (e.g. "Facebook, Inc." and "Meta Platforms").
- A parent and its subsidiary are NOT the same entity (e.g. "Amazon" and "Amazon Web Services").
- Different companies with similar names are NOT the same entity.
- If unsure, answer false.

Record A: name={a_name!r}, website={a_site!r}
Record B: name={b_name!r}, website={b_site!r}

Return JSON only: {{"match": true or false, "confidence": 0.0 to 1.0, "reason": "short"}}"""

_cache = None
_client = None
calls_made = 0  # API calls (cache misses) in this process, for cost reporting


def _load():
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    return _cache


def _key(a, b):
    left = (a["name"], a.get("website") or "")
    right = (b["name"], b.get("website") or "")
    pair = sorted([left, right])  # order-independent
    raw = json.dumps([PROMPT_VERSION, MODEL, pair])
    return hashlib.sha1(raw.encode()).hexdigest()


def save_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(_load(), indent=0))


def llm_match(a, b) -> dict:
    """Returns {"match": bool, "confidence": float, "reason": str, "cached": bool}."""
    global _client, calls_made
    cache = _load()
    key = _key(a, b)
    if key in cache:
        return {**cache[key], "cached": True}

    if _client is None:
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv()
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = PROMPT.format(a_name=a["name"], a_site=a.get("website") or "",
                           b_name=b["name"], b_site=b.get("website") or "")
    start = time.perf_counter()
    res = _client.chat.completions.create(
        model=MODEL, temperature=0, response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}])
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    calls_made += 1
    try:
        data = json.loads(res.choices[0].message.content)
        result = {"match": bool(data.get("match", False)),
                  "confidence": float(data.get("confidence", 0.0)),
                  "reason": str(data.get("reason", ""))}
    except (ValueError, TypeError):
        result = {"match": False, "confidence": 0.0, "reason": "unparseable LLM response"}
    # recorded once at call time, so cached re-runs can still report real latency and cost
    result["latency_ms"] = latency_ms
    result["tokens_in"] = res.usage.prompt_tokens
    result["tokens_out"] = res.usage.completion_tokens
    cache[key] = result
    return {**result, "cached": False}
