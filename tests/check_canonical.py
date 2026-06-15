from src.db.postgres import SessionLocal
from src.db.models import CompanyMapping, CanonicalCompany

session = SessionLocal()

print("\nCANONICAL COMPANIES:")
for c in session.query(CanonicalCompany).all():
    print(c.id, c.canonical_name)

print("\nMAPPINGS:")
for m in session.query(CompanyMapping).all():
    print(m.company_id, "->", m.canonical_company_id, m.match_score)