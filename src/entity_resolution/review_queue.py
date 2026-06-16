from src.db.postgres import SessionLocal
from src.db.models import ReviewQueue


def add_to_review_queue(company_a, company_b, score):

    session = SessionLocal()

    item = ReviewQueue(
        company_a=company_a,
        company_b=company_b,
        score=score,
        status="PENDING"
    )

    session.add(item)
    session.commit()

    return item.id


def approve_match(review_id):

    session = SessionLocal()

    item = session.get(ReviewQueue, review_id)

    if item:
        item.status = "APPROVED"
        session.commit()

    return item


def reject_match(review_id):

    session = SessionLocal()

    item = session.get(ReviewQueue, review_id)

    if item:
        item.status = "REJECTED"
        session.commit()

    return item