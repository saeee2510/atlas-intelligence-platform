from src.entity_resolution.relationship_extractor import run_extraction
from src.db.postgres import SessionLocal
from src.db.models import CanonicalCompany, CompanyRelationship


def test_relationship_extraction():

    # sample text
    text = """
    Microsoft and Google are competitors in cloud computing.
    OpenAI partners with Microsoft on AI research.
    Google acquired DeepMind in AI development.
    """

    run_extraction(text)

    session = SessionLocal()

    print("\n=== CANONICAL COMPANIES ===")
    for c in session.query(CanonicalCompany).all():
        print(c.id, c.canonical_name)

    print("\n=== RELATIONSHIPS ===")
    for r in session.query(CompanyRelationship).all():
        print(
            r.source_company,
            "->",
            r.target_company,
            r.relationship_type,
            r.confidence
        )


if __name__ == "__main__":
    test_relationship_extraction()