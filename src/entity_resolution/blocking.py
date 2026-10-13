"""
Blocking: only compare records that share at least one cheap key, instead of
all n*(n-1)/2 pairs.

Keys per record:
  tok:<first normalized token>      "microsoft corp" -> tok:microsoft
  pre:<first 4 chars, no spaces>    catches "open ai" / "openai", most typos
  acr:<initialism or short name>    "IBM" and "International Business Machines" share acr:ibm
  dom:<domain>                      same website

Optional semantic blocking adds each record's k nearest neighbors by
embedding, which catches tickers and renames ("MSFT", "Facebook") that share
no characters with the canonical name.
"""
from itertools import combinations

from src.entity_resolution.embedding_cache import cosine
from src.processing.normalize import (compact, initialisms, normalize_domain,
                                      normalize_name, raw_compact)


def blocking_key(name: str) -> str:
    """Prefix key, kept for backwards compatibility."""
    return compact(name)[:4]


def blocking_keys(record: dict) -> set:
    name = record["name"]
    tokens = normalize_name(name).split()
    keys = set()
    if tokens:
        keys.add(f"tok:{tokens[0]}")
    c = compact(name)
    if len(c) >= 3:
        keys.add(f"pre:{c[:4]}")
    short = raw_compact(name)
    if 2 <= len(short) <= 5:
        keys.add(f"acr:{short}")
    keys |= {f"acr:{i}" for i in initialisms(name)}
    domain = normalize_domain(record.get("website"))
    if domain:
        keys.add(f"dom:{domain}")
    return keys


def candidate_pairs(records, embeddings=None, k_neighbors=0):
    """Index pairs (i, j), i < j, that share a key or are embedding neighbors."""
    index = {}
    for i, r in enumerate(records):
        for key in blocking_keys(r):
            index.setdefault(key, []).append(i)
    pairs = set()
    for members in index.values():
        pairs.update(combinations(sorted(set(members)), 2))

    if embeddings and k_neighbors:
        vecs = [embeddings.get(r["name"]) for r in records]
        for i, vi in enumerate(vecs):
            if vi is None:
                continue
            sims = sorted(((cosine(vi, vj), j) for j, vj in enumerate(vecs) if j != i and vj is not None),
                          reverse=True)[:k_neighbors]
            pairs.update((min(i, j), max(i, j)) for _, j in sims)
    return pairs


def evaluate_blocking(labeled_pairs, embeddings=None, k_neighbors=0):
    """Pair completeness (share of true matches kept) and reduction ratio
    (share of all comparisons avoided), over the benchmark's unique names."""
    names = sorted({p["a_name"] for p in labeled_pairs} | {p["b_name"] for p in labeled_pairs})
    pos = {n: i for i, n in enumerate(names)}
    records = [{"name": n} for n in names]
    candidates = candidate_pairs(records, embeddings, k_neighbors)
    matches = [p for p in labeled_pairs if p["label"] == 1]
    kept = sum(1 for p in matches
               if (min(pos[p["a_name"]], pos[p["b_name"]]), max(pos[p["a_name"]], pos[p["b_name"]])) in candidates)
    total = len(names) * (len(names) - 1) // 2
    return {"records": len(names), "all_pairs": total, "candidate_pairs": len(candidates),
            "reduction_ratio": round(1 - len(candidates) / total, 4),
            "pair_completeness": round(kept / len(matches), 4) if matches else None}
