import os
import json
from openai import OpenAI
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- LLM CALL ----------
def _call_llm(description: str):
    prompt = f"""
You are a company enrichment system.

Given a company description, extract structured metadata.

Return ONLY valid JSON:

{{
  "industry": "",
  "subcategory": "",
  "business_model": "",
  "company_size": ""
}}

Rules:
- industry: high-level (Tech, Finance, Healthcare, etc.)
- subcategory: more specific domain
- business_model: B2B, B2C, SaaS, Marketplace, etc.
- company_size: Startup, SMB, Enterprise

Description:
{description}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return res.choices[0].message.content


# ---------- CACHE LAYER ----------
@lru_cache(maxsize=1000)
def enrich_company(description: str):
    raw = _call_llm(description)

    try:
        data = json.loads(raw)
    except Exception:
        return {
            "industry": None,
            "subcategory": None,
            "business_model": None,
            "company_size": None
        }

    return data