from rapidfuzz import fuzz

from src.processing.normalize import normalize_name


def fuzzy_score(a: str, b: str) -> float:
    return fuzz.token_set_ratio(normalize_name(a), normalize_name(b)) / 100
