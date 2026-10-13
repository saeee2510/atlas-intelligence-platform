"""
Canonicalization: group raw company records into canonical companies.

For each raw record, only canonical companies that share a blocking key are
compared (instead of every canonical). The resolver decides; uncertain LLM
decisions are written to the human review queue.
"""
from src.db.models import CanonicalCompany, Company, CompanyMapping, ReviewQueue
from src.db.postgres import SessionLocal
from src.entity_resolution.blocking import blocking_keys
from src.entity_resolution.llm_enrich import enrich_company
from src.entity_resolution.resolver import resolve


def canonicalize():
    session = SessionLocal()
    companies = session.query(Company).order_by(Company.id).all()
    print(f"Canonicalizing {len(companies)} companies")

    canonicals = []      # (CanonicalCompany, representative Company, blocking keys)
    key_index = {}       # blocking key -> indexes into canonicals
    comparisons = 0

    for company in companies:
        record = {"name": company.name, "website": company.website}
        keys = blocking_keys(record)
        candidate_ids = sorted({i for k in keys for i in key_index.get(k, [])})

        best, best_result = None, None
        for i in candidate_ids:
            canonical, rep, _ = canonicals[i]
            comparisons += 1
            result = resolve(record, {"name": rep.name, "website": rep.website})
            if result["needs_review"]:
                session.add(ReviewQueue(company_a=company.id, company_b=rep.id,
                                        score=result["score"], status="PENDING"))
            if result["match"] and (best_result is None or result["score"] > best_result["score"]):
                best, best_result = i, result

        if best is not None:
            session.add(CompanyMapping(company_id=company.id,
                                       canonical_company_id=canonicals[best][0].id,
                                       match_score=best_result["score"]))
            continue

        enriched = enrich_company(company.description or company.name)
        canonical = CanonicalCompany(
            canonical_name=company.name, website=company.website,
            industry=enriched.get("industry"), subcategory=enriched.get("subcategory"),
            business_model=enriched.get("business_model"), company_size=enriched.get("company_size"),
            confidence=1.0)
        session.add(canonical)
        session.flush()
        canonicals.append((canonical, company, keys))
        for k in keys:
            key_index.setdefault(k, []).append(len(canonicals) - 1)
        session.add(CompanyMapping(company_id=company.id, canonical_company_id=canonical.id, match_score=1.0))

    session.commit()
    total = len(companies) * (len(companies) - 1) // 2
    print(f"Done: {len(canonicals)} canonical companies, {comparisons} comparisons "
          f"(all-pairs would be up to {total})")


if __name__ == "__main__":
    canonicalize()
