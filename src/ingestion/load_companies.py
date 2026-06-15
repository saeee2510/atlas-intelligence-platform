import pandas as pd

from src.db.postgres import SessionLocal, init_db
from src.db.models import Company
from src.processing.normalize import normalize_name

from src.entity_resolution.embedding_store import get_embedding
from src.entity_resolution.embedding_cache import get_cached_embedding, save_cache


def load_data():
    init_db()
    session = SessionLocal()

    df = pd.read_csv("data/raw/companies.csv")

    for _, row in df.iterrows():

        name = row["name"]

        # 1. Normalize
        normalized = normalize_name(name)

        # 2. Embedding (cached + safe)
        embedding = get_cached_embedding(
            row["name"],
            get_embedding
        )

        embedding = list(embedding)  # pgvector requirement

        # 3. Create DB object
        c = Company(
            name=name,
            normalized_name=normalized,
            website=row.get("website"),
            description=row.get("description"),
            embedding=embedding
        )

        session.add(c)

    # 4. Commit once (important: performance)
    session.commit()
    session.close()

    # 5. Persist embedding cache
    save_cache()

    print("Data loaded successfully with embeddings")


if __name__ == "__main__":
    load_data()