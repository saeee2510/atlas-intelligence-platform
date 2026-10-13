"""
Loads company records into Postgres with cached embeddings.

    python -m src.ingestion.load_companies              # data/raw/companies.csv (7 demo rows)
    python -m src.ingestion.load_companies --benchmark  # every unique record in the benchmark (~200)
"""
import argparse

import pandas as pd

from src.db.models import Company
from src.db.postgres import SessionLocal, init_db
from src.entity_resolution.embedding_cache import embed_many
from src.evaluation.build_benchmark import load as load_benchmark
from src.processing.normalize import normalize_name


def _rows(benchmark: bool):
    if not benchmark:
        df = pd.read_csv("data/raw/companies.csv").fillna("")
        return df.to_dict("records")
    seen, rows = {}, []
    for p in load_benchmark():
        for name, site in ((p["a_name"], p["a_website"]), (p["b_name"], p["b_website"])):
            if name not in seen:
                seen[name] = True
                rows.append({"name": name, "website": site, "description": ""})
    return rows


def load_data(benchmark: bool = False):
    init_db()
    session = SessionLocal()
    rows = _rows(benchmark)
    vectors = embed_many([r["name"] for r in rows])
    for r in rows:
        session.add(Company(name=r["name"], normalized_name=normalize_name(r["name"]),
                            website=r.get("website") or None, description=r.get("description") or None,
                            embedding=vectors.get(r["name"])))
    session.commit()
    session.close()
    print(f"Loaded {len(rows)} companies with embeddings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true")
    load_data(parser.parse_args().benchmark)
