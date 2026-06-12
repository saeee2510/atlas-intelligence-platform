from rapidfuzz import fuzz

def fuzzy_score(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a, b) / 100