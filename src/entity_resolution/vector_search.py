# src/entity_resolution/vector_search.py

from src.db.postgres import SessionLocal
from src.db.models import Company
from src.entity_resolution.embedding_store import get_embedding


def cosine_search_candidates(query_text, limit=10):
    """
    Step 1: embed query
    Step 2: run pgvector similarity search
    Step 3: return top-k candidates
    """

    session = SessionLocal()

    # 1. get query embedding
    query_embedding = get_embedding(query_text)

    # 2. similarity search using pgvector
    candidates = (
        session.query(Company)
        .order_by(Company.embedding.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )

    # 3. format output
    results = []
    for c in candidates:
        results.append({
            "id": c.id,
            "name": c.name,
            "website": c.website
        })

    return results