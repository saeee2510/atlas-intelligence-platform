from src.db.postgres import SessionLocal
from src.db.models import Company
from src.entity_resolution.resolver import resolve

def run():
    session = SessionLocal()

    companies = session.query(Company).all()

    for i in range(len(companies)):
        for j in range(i+1, len(companies)):

            a = companies[i]
            b = companies[j]

            result = resolve(
                {"name": a.name, "website": a.website},
                {"name": b.name, "website": b.website}
            )

            print(a.name, " <-> ", b.name, result)

if __name__ == "__main__":
    run()