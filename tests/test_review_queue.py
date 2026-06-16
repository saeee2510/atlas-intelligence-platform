from src.db.postgres import SessionLocal
from src.db.models import Company
from src.entity_resolution.review_queue import (
    add_to_review_queue,
    approve_match
)

session = SessionLocal()

companies = session.query(Company).limit(2).all()

review_id = add_to_review_queue(
    company_a=companies[0].id,
    company_b=companies[1].id,
    score=0.67
)

print("Created:", review_id)

approve_match(review_id)

print("Approved")