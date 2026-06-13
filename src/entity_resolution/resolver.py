import json
import numpy as np
from rapidfuzz import fuzz

from src.entity_resolution.embedding_store import get_embedding
from src.entity_resolution.llm_judge import llm_match


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def resolve(a, b):

    # 1. fuzzy score
    fuzzy = fuzz.token_set_ratio(a["name"], b["name"]) / 100

    # 2. embedding score
    emb_a = get_embedding(a["name"])
    emb_b = get_embedding(b["name"])
    emb_score = cosine(emb_a, emb_b)

    # 3. website match
    website = 1.0 if a.get("website") == b.get("website") else 0.0

    # 4. weighted score
    score = 0.2 * fuzzy + 0.6 * emb_score + 0.2 * website

    result = {
        "match": score > 0.75,
        "score": round(score, 4),
        "used_llm": False
    }

    # 5. LLM fallback (uncertain zone)
    if 0.55 < score < 0.80:
        llm_raw = llm_match(a, b)

        # llm_match returns JSON string → convert to dict
        llm_result = json.loads(llm_raw)

        return {
            "match": llm_result["match"],
            "score": round(score, 4),
            "confidence": llm_result.get("confidence"),
            "reason": llm_result.get("reason"),
            "used_llm": True
        }

    return result