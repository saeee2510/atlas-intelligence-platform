import re

STOPWORDS = [
    "inc", "corp", "corporation", "llc", "ltd", "co", "company"
]

def normalize_name(name: str) -> str:
    if not name:
        return ""

    name = name.lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)

    tokens = [t for t in name.split() if t not in STOPWORDS]

    return " ".join(tokens).strip()