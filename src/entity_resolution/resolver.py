import json
import numpy as np
from rapidfuzz import fuzz

from src.entity_resolution.embedding_store import get_embedding
from src.entity_resolution.llm_judge import llm_match
from src.entity_resolution.review_queue import add_to_review_queue

ALIASES = {
    "msft": "microsoft",
    "google llc": "google",
    
    "open ai": "openai"
}

def normalize(name: str) -> str:
    return ALIASES.get(name.lower(), name.lower())


def cosine(a, b):
    return float(
        np.dot(a, b) /
        (np.linalg.norm(a) * np.linalg.norm(b))
    )


def resolve(a, b):
    """
    Resolve whether two company records represent the same entity.

    Inputs:
    {
        "id": 1,
        "name": "...",
        "website": "..."
    }

    Returns:
    {
        "match": bool,
        "score": float,
        "used_llm": bool
    }
    """

    # ----------------------------------
    # 1. Fuzzy match score
    # ----------------------------------
    fuzzy = fuzz.token_set_ratio(
        normalize(a["name"]),
        normalize(b["name"])
) / 100

    # ----------------------------------
    # 2. Embedding similarity
    # ----------------------------------
    emb_a = get_embedding(f"{a['name']} {a.get('website','')}")
    emb_b = get_embedding(f"{b['name']} {b.get('website','')}")

    emb_score = cosine(
        emb_a,
        emb_b
    )

    # ----------------------------------
    # 3. Website match rule
    # ----------------------------------
    website = (
        1.0
        if a.get("website") == b.get("website")
        and a.get("website") is not None
        else 0.0
    )

    # ----------------------------------
    # 4. Final weighted score
    # ----------------------------------
    score = (
        0.40 * fuzzy +
        0.40 * emb_score +
        0.20 * website
)

    score = round(score, 4)

    # ----------------------------------
    # 5. Human review zone
    # ----------------------------------
    if 0.55 < score < 0.72:

        # add to review queue
        if a.get("id") and b.get("id"):
            add_to_review_queue(
                company_a=a["id"],
                company_b=b["id"],
                score=score
            )

        # ask LLM for adjudication
        llm_raw = llm_match(a, b)

        try:
            llm_result = json.loads(llm_raw)

            return {
                "match": llm_result.get("match", False),
                "score": score,
                "confidence": llm_result.get("confidence"),
                "reason": llm_result.get("reason"),
                "used_llm": True
            }

        except Exception:

            return {
                "match": False,
                "score": score,
                "used_llm": True,
                "reason": "Failed to parse LLM response"
            }

    # ----------------------------------
    # 6. High-confidence auto match
    # ----------------------------------
    if score >= 0.72:
        return {
            "match": True,
            "score": score,
            "used_llm": False
        }

    # ----------------------------------
    # 7. Low-confidence reject
    # ----------------------------------
    return {
        "match": False,
        "score": score,
        "used_llm": False
    }