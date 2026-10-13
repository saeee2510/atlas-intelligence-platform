"""
Pairwise features for entity resolution. Every feature is in [0, 1].

  fuzzy          token-set similarity of normalized names (order-insensitive)
  compact_ratio  character similarity with spaces removed ('Open AI' vs 'OpenAI')
  acronym        1 if one name is an initialism of the other ('IBM' vs 'International Business Machines')
  website_same   1 if both records have a website and the domains are equal
  website_diff   1 if both records have a website and the domains differ (strong negative signal)
  embedding      cosine similarity of name embeddings (semantic: tickers, rebrands)
"""
from rapidfuzz import fuzz

from src.processing.normalize import (compact, initialisms, normalize_domain,
                                      normalize_name, raw_compact)

RULE_FEATURES = ["fuzzy", "compact_ratio", "acronym", "website_same", "website_diff"]
ALL_FEATURES = RULE_FEATURES + ["embedding"]


def acronym_match(name_a: str, name_b: str) -> bool:
    for short, long in ((name_a, name_b), (name_b, name_a)):
        s = raw_compact(short)
        if 2 <= len(s) <= 5 and len(short.split()) <= 2 and s in initialisms(long):
            return True
    return False


def pair_features(a: dict, b: dict, embedding_sim=None) -> dict:
    na, nb = normalize_name(a["name"]), normalize_name(b["name"])
    da, db = normalize_domain(a.get("website")), normalize_domain(b.get("website"))
    both_sites = bool(da and db)
    f = {
        "fuzzy": fuzz.token_set_ratio(na, nb) / 100 if na and nb else 0.0,
        "compact_ratio": fuzz.ratio(compact(a["name"]), compact(b["name"])) / 100,
        "acronym": 1.0 if acronym_match(a["name"], b["name"]) else 0.0,
        "website_same": 1.0 if both_sites and da == db else 0.0,
        "website_diff": 1.0 if both_sites and da != db else 0.0,
    }
    if embedding_sim is not None:
        f["embedding"] = max(0.0, float(embedding_sim))
    return f
