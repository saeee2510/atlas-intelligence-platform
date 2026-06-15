import json
from openai import OpenAI

from src.db.postgres import SessionLocal
from src.db.models import CompanyRelationship, CanonicalCompany

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- LLM EXTRACTION ----------
def extract_relationships(text: str):
    prompt = f"""
You are an information extraction system.

Extract company relationships from the text.

Return ONLY valid JSON in this format:
[
  {{
    "source_company": "...",
    "target_company": "...",
    "relationship_type": "competitor | partner | acquired | subsidiary | investor",
    "confidence": 0.0-1.0
  }}
]

Text:
{text}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return res.choices[0].message.content


# ---------- CANONICAL MATCH ----------
def get_canonical(session, name):
    return session.query(CanonicalCompany).filter(
        CanonicalCompany.canonical_name.ilike(f"%{name}%")
    ).first()


# ---------- PIPELINE ----------
def run_extraction(text: str):
    session = SessionLocal()

    raw_output = extract_relationships(text)

    import json

    # 1. Parse LLM output safely
    try:
        data = json.loads(raw_output)
    except Exception:
        print(" Failed to parse LLM output:", raw_output)
        return

    # 2. Handle double-encoded JSON (LLM sometimes returns stringified JSON)
    if isinstance(data, str):
        data = json.loads(data)

    # 3. Ensure list format
    if isinstance(data, dict):
        data = data.get("relationships", [])

    # 4. Process records safely
    for r in data:

        if not isinstance(r, dict):
            continue

        source = get_canonical(session, r.get("source_company"))
        target = get_canonical(session, r.get("target_company"))

        if not source or not target:
            continue

        edge = CompanyRelationship(
            source_company=source.id,
            target_company=target.id,
            relationship_type=r.get("relationship_type"),
            confidence=float(r.get("confidence", 0.0))
        )

        session.add(edge)

    session.commit()
    print(" Relationships stored in knowledge graph")