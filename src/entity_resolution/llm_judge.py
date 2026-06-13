from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def llm_match(a, b):
    prompt = f"""
You are deciding whether two company records refer to the same company.

Company A:
Name: {a['name']}
Website: {a.get('website')}
Description: {a.get('description')}

Company B:
Name: {b['name']}
Website: {b.get('website')}
Description: {b.get('description')}

Return JSON:
{{
  "match": true/false,
  "confidence": 0-1,
  "reason": "short explanation"
}}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return res.choices[0].message.content