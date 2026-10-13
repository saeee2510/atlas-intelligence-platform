"""
Hybrid entity resolver: cheap signals decide the easy pairs, the LLM decides
only the uncertain ones.

    features (fuzzy, compact, acronym, website, embedding)
        -> learned logistic score p(match)
        -> p >= band_high          : auto-match   (no LLM)
           p <= band_low           : auto-reject  (no LLM)
           band_low < p < band_high: LLM judge decides; low-confidence LLM
                                     answers are flagged for human review

The weights and thresholds are learned on the benchmark's dev split by
src/evaluation/run_ablation.py and saved to data/benchmark/model.json.
This function has no side effects: callers decide what to do with
"needs_review" (canonicalization writes those pairs to the review queue).
"""
from src.entity_resolution import embedding_cache, llm_judge
from src.entity_resolution import model as scoring_model
from src.processing.features import ALL_FEATURES, pair_features

REVIEW_CONFIDENCE = 0.7

# used only until run_ablation.py has trained a real model
DEFAULT_CONFIG = {
    "model": {"features": ALL_FEATURES, "bias": -6.0,
              "weights": {"fuzzy": 4.0, "compact_ratio": 2.0, "acronym": 4.0,
                          "website_same": 3.0, "website_diff": -4.0, "embedding": 3.0}},
    "band_low": 0.2, "band_high": 0.8, "threshold": 0.5, "use_llm": True,
}

_config = None


def get_config():
    global _config
    if _config is None:
        saved = scoring_model.load()
        _config = saved if saved else DEFAULT_CONFIG
    return _config


def score_pair(a, b, config=None, embedding_sim=None):
    config = config or get_config()
    if "embedding" in config["model"]["features"] and embedding_sim is None:
        vecs = embedding_cache.embed_many([a["name"], b["name"]])
        embedding_sim = embedding_cache.cosine(vecs.get(a["name"]), vecs.get(b["name"]))
    feats = pair_features(a, b, embedding_sim)
    return scoring_model.predict_proba(config["model"], feats), feats


def resolve(a, b, config=None, use_llm=None, embedding_sim=None) -> dict:
    config = config or get_config()
    use_llm = config.get("use_llm", True) if use_llm is None else use_llm
    p, feats = score_pair(a, b, config, embedding_sim)
    result = {"score": round(p, 4), "features": feats, "used_llm": False, "needs_review": False}

    if not use_llm:
        return {**result, "match": p >= config["threshold"], "decision": "model"}
    if p >= config["band_high"]:
        return {**result, "match": True, "decision": "auto_match"}
    if p <= config["band_low"]:
        return {**result, "match": False, "decision": "auto_reject"}

    verdict = llm_judge.llm_match(a, b)
    return {**result, "match": verdict["match"], "used_llm": True,
            "decision": "llm_match" if verdict["match"] else "llm_reject",
            "llm_confidence": verdict["confidence"], "reason": verdict["reason"],
            "needs_review": verdict["confidence"] < REVIEW_CONFIDENCE}
