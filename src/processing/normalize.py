"""
Name and website normalization for entity resolution.

normalize_name("The Procter & Gamble Company") -> "procter and gamble"
compact("Wal-Mart Stores, Inc.")                -> "walmartstores"
initialisms("International Business Machines")  -> {"ibm"}
normalize_domain("https://www.IBM.com/us")      -> "ibm.com"
"""
import re

LEGAL_SUFFIXES = {
    "inc", "incorporated", "corp", "corporation", "llc", "ltd", "limited", "co",
    "company", "plc", "group", "holdings", "pbc", "lp", "sa", "ag", "gmbh", "com",
}
CONNECTORS = {"and", "of", "the", "for"}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower().replace("&", " and ")
    name = re.sub(r"\(.*?\)", " ", name)          # drop parentheticals
    name = re.sub(r"[^a-z0-9 ]", " ", name)       # punctuation -> space
    tokens = name.split()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens = tokens[:-1]
    return " ".join(tokens)


def compact(name: str) -> str:
    """Normalized name with spaces removed, so 'Open AI' == 'OpenAI'."""
    return normalize_name(name).replace(" ", "")


def raw_compact(name: str) -> str:
    """Letters and digits only, before suffix removal: 'P&G' -> 'pg', 'BofA' -> 'bofa'."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def initialisms(name: str) -> set:
    """Plausible initialisms of a multi-word name.

    'bank of america' -> {'boa', 'ba', 'bofa'}; 'procter and gamble' -> {'pag', 'pg', 'pandg'}
    """
    tokens = normalize_name(name).split()
    if len(tokens) < 2:
        return set()
    every_word = "".join(t[0] for t in tokens)
    content_words = "".join(t[0] for t in tokens if t not in CONNECTORS)
    connectors_spelled = "".join(t if t in CONNECTORS else t[0] for t in tokens)
    return {every_word, content_words, connectors_spelled} - {""}


def normalize_domain(website: str) -> str:
    if not website:
        return ""
    w = website.strip().lower()
    w = re.sub(r"^https?://", "", w)
    w = w.split("/")[0]
    if w.startswith("www."):
        w = w[4:]
    return w
