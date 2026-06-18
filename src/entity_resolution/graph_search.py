from src.db.postgres import SessionLocal
from src.db.models import CanonicalCompany, CompanyRelationship


def get_company_graph(company_name: str):

    session = SessionLocal()

    company = session.query(CanonicalCompany).filter(
        CanonicalCompany.canonical_name.ilike(f"%{company_name}%")
    ).first()

    if not company:
        return None

    graph = {
        "company": company.canonical_name,
        "relations": []
    }

    # -----------------------------
    # OUTGOING EDGES
    # -----------------------------
    outgoing = session.query(CompanyRelationship).filter(
        CompanyRelationship.source_company == company.id
    ).all()

    for r in outgoing:

        target = session.query(CanonicalCompany).filter(
            CanonicalCompany.id == r.target_company
        ).first()

        if target:
            graph["relations"].append({
                "direction": "out",
                "type": r.relationship_type,
                "company": target.canonical_name,
                "confidence": r.confidence
            })

    # -----------------------------
    # INCOMING EDGES  
    # -----------------------------
    incoming = session.query(CompanyRelationship).filter(
        CompanyRelationship.target_company == company.id
    ).all()

    for r in incoming:

        source = session.query(CanonicalCompany).filter(
            CanonicalCompany.id == r.source_company
        ).first()

        if source:
            graph["relations"].append({
                "direction": "in",
                "type": r.relationship_type,
                "company": source.canonical_name,
                "confidence": r.confidence
            })

    return graph