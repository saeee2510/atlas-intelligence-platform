import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from src.db.postgres import SessionLocal
from src.db.models import CompanyRelationship, CanonicalCompany

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================
#  LAYER 2: CORPORATE HIERARCHY MAP
# =========================
CORPORATE_MAP = {
    "google llc": "alphabet inc",
    "youtube": "alphabet inc",
    "deepmind": "alphabet inc"
}


# =========================
# LLM EXTRACTION
# =========================
def extract_relationships(text: str):

    prompt = f"""
Extract company relationships from the text.

Return ONLY valid JSON list:

[
  {{
    "source_company": "...",
    "target_company": "...",
    "relationship_type": "competitor | partner | acquired | subsidiary | investor",
    "confidence": 0.0
  }}
]

Text:
{text}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content


# =========================
# CANONICAL RESOLUTION
# =========================
def get_canonical(session, name):

    if not name:
        return None

    name = name.lower()

    candidates = session.query(CanonicalCompany).all()

    for c in candidates:
        if c.canonical_name and (
            name in c.canonical_name.lower()
            or c.canonical_name.lower() in name
        ):
            return c

    return None


# =========================
# MAIN PIPELINE
# =========================
def run_extraction(text: str):

    session = SessionLocal()

    raw_output = extract_relationships(text)

    # -------------------------
    # Parse LLM output
    # -------------------------
    try:
        data = json.loads(raw_output)
    except Exception:
        print("Failed to parse LLM output:\n", raw_output)
        return

    if isinstance(data, dict):
        data = data.get("relationships", [])

    if not isinstance(data, list):
        print("Unexpected format:", data)
        return

    inserted = 0

    # =========================
    # PROCESS RELATIONSHIPS
    # =========================
    for r in data:

        if not isinstance(r, dict):
            continue

        source = get_canonical(session, r.get("source_company"))
        target = get_canonical(session, r.get("target_company"))

        if not source or not target:
            continue

        # -------------------------
        # LLM RELATIONSHIP EDGE
        # -------------------------
        existing = session.query(CompanyRelationship).filter(
            CompanyRelationship.source_company == source.id,
            CompanyRelationship.target_company == target.id,
            CompanyRelationship.relationship_type == r.get("relationship_type")
        ).first()

        if not existing:
            session.add(CompanyRelationship(
                source_company=source.id,
                target_company=target.id,
                relationship_type=r.get("relationship_type"),
                confidence=float(r.get("confidence", 0.0))
            ))
            inserted += 1

        # -------------------------
        # LAYER 2: CORPORATE HIERARCHY INJECTION
        # -------------------------
        parent_name = CORPORATE_MAP.get(source.canonical_name.lower())

        if parent_name:

            parent = get_canonical(session, parent_name)

            if parent:

                existing_parent = session.query(CompanyRelationship).filter(
                    CompanyRelationship.source_company == source.id,
                    CompanyRelationship.target_company == parent.id,
                    CompanyRelationship.relationship_type == "subsidiary"
                ).first()

                if not existing_parent:
                    session.add(CompanyRelationship(
                        source_company=source.id,
                        target_company=parent.id,
                        relationship_type="subsidiary",
                        confidence=1.0
                    ))
                    inserted += 1

    session.commit()

    print(f"Relationships stored in knowledge graph: {inserted}")