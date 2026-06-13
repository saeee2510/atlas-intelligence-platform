import re

STOPWORDS = [
    "inc", "corp", "corporation", "llc", "ltd", "co", "company"
]

def normalize_name(name: str) -> str:
    if not name:
        return ""

    name = name.lower()
    name = re.sub(r"[^a-z0-9 ]", "", name)

    return name.strip()