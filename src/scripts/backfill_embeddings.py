from src.db.postgres import SessionLocal
from src.db.models import Company
from src.entity_resolution.embedding_store import get_embedding

def backfill():
    session = SessionLocal()

    companies = session.query(Company).all()

    for c in companies:
        if c.embedding is None:
            emb = get_embedding(c.name)
            c.embedding = emb

    session.commit()
    print("Embeddings backfilled")

if __name__ == "__main__":
    backfill()