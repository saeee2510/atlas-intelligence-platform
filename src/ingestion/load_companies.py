import pandas as pd
from src.db.postgres import SessionLocal, init_db
from src.db.models import Company
from src.processing.normalize import normalize_name

def load_data():
    init_db()
    session = SessionLocal()

    df = pd.read_csv("data/raw/companies.csv")

    for _, row in df.iterrows():
        c = Company(
            name=row["name"],
            normalized_name=normalize_name(row["name"]),
            website=row.get("website"),
            description=row.get("description")
        )
        session.add(c)

    session.commit()
    session.close()

if __name__ == "__main__":
    load_data()