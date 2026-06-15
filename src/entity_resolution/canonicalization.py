from src.db.postgres import SessionLocal
from src.db.models import (
    Company,
    CanonicalCompany,
    CompanyMapping
)
from src.entity_resolution.resolver import resolve


THRESHOLD = 0.60  # key fix: clustering threshold


def canonicalize():

    print("STARTING CANONICALIZATION")

    session = SessionLocal()

    companies = session.query(Company).all()
    print("Companies:", len(companies))

    # IMPORTANT FIX: load once (not inside loop)
    canonicals = session.query(CanonicalCompany).all()

    for company in companies:

        best_match = None
        best_score = 0

        # find best canonical match
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

            score = result["score"]

            if score > best_score:
                best_score = score
                best_match = canonical

        # CASE 1: MATCH FOUND → attach to existing canonical
        if best_match and best_score >= THRESHOLD:

            session.add(CompanyMapping(
                company_id=company.id,
                canonical_company_id=best_match.id,
                match_score=best_score
            ))

        # CASE 2: NO MATCH → create new canonical
        else:

            new_canonical = CanonicalCompany(
                canonical_name=company.name,
                website=company.website,
                industry=None,
                confidence=1.0
            )

            session.add(new_canonical)
            session.flush()

            # IMPORTANT: update canonicals list so future matches see it
            canonicals.append(new_canonical)

            session.add(CompanyMapping(
                company_id=company.id,
                canonical_company_id=new_canonical.id,
                match_score=1.0
            ))

    session.commit()
    print("Canonicalization complete")