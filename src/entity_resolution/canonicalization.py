from src.db.postgres import SessionLocal
from src.db.models import (
    Company,
    CanonicalCompany,
    CompanyMapping
)
from src.entity_resolution.resolver import resolve



def canonicalize():

    print("STARTING CANONICALIZATION")

    session = SessionLocal()

    companies = session.query(Company).all()

    print("Companies:", len(companies))

    for company in companies:

        canonicals = session.query(CanonicalCompany).all()

        best_match = None
        best_score = 0

        for canonical in canonicals:

            result = resolve(
                {
                    "name": company.name,
                    "website": company.website
                },
                {
                    "name": canonical.canonical_name,
                    "website": canonical.website
                }
            )

            if result["score"] > best_score:
                best_score = result["score"]
                best_match = canonical

        if best_match and best_score > 0.75:

            session.add(CompanyMapping(
                company_id=company.id,
                canonical_company_id=best_match.id,
                match_score=best_score
            ))

        else:

            new_canonical = CanonicalCompany(
                canonical_name=company.name,
                website=company.website,
                industry=None,
                confidence=1.0
            )

            session.add(new_canonical)
            session.flush()

            session.add(CompanyMapping(
                company_id=company.id,
                canonical_company_id=new_canonical.id,
                match_score=1.0
            ))

    session.commit()
    print("Canonicalization complete")