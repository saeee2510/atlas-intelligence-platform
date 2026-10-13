"""Prints tables, canonical companies, mappings, and the review queue."""
from sqlalchemy import inspect

from src.db.models import CanonicalCompany, CompanyMapping, ReviewQueue
from src.db.postgres import SessionLocal, engine

print("TABLES:", inspect(engine).get_table_names())
session = SessionLocal()
print("\nCANONICAL COMPANIES:")
for c in session.query(CanonicalCompany).all():
    print(f"  {c.id}: {c.canonical_name}")
print("\nMAPPINGS (company -> canonical, score):")
for m in session.query(CompanyMapping).all():
    print(f"  {m.company_id} -> {m.canonical_company_id} ({m.match_score:.3f})")
print("\nREVIEW QUEUE:")
for r in session.query(ReviewQueue).all():
    print(f"  {r.company_a} vs {r.company_b}: {r.score:.3f} [{r.status}]")
