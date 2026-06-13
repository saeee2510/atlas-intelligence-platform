from src.entity_resolution.fuzzy_match import fuzzy_score
from src.entity_resolution.embedding_match import embed, cosine_sim


def resolve(entity_a, entity_b):
    name_score = fuzzy_score(
        entity_a["name"],
        entity_b["name"]
    )

    emb_a = embed(entity_a["name"])
    emb_b = embed(entity_b["name"])

    emb_score = cosine_sim(emb_a, emb_b)

    website_match = (
        entity_a.get("website")
        == entity_b.get("website")
    )

    final_score = (
        0.4 * name_score +
        0.4 * emb_score +
        0.2 * (1.0 if website_match else 0.0)
    )

    return {
        "match": final_score > 0.75,
        "score": round(final_score, 3)
    }