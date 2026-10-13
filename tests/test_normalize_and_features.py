from src.processing.features import acronym_match, pair_features
from src.processing.normalize import compact, initialisms, normalize_domain, normalize_name


def test_normalize_strips_legal_suffixes_and_punctuation():
    assert normalize_name("Microsoft Corp") == "microsoft"
    assert normalize_name("Apple Inc.") == "apple"
    assert normalize_name("Tesla, Inc") == "tesla"
    assert normalize_name("Google LLC") == "google"
    assert normalize_name("The Procter & Gamble Company") == "procter and gamble"
    assert normalize_name("Amazon.com, Inc.") == "amazon"


def test_compact_ignores_spacing():
    assert compact("Open AI") == compact("OpenAI")


def test_initialisms():
    assert "ibm" in initialisms("International Business Machines Corporation")
    assert "bofa" in initialisms("Bank of America")
    assert "pg" in initialisms("Procter & Gamble")


def test_acronym_match_and_lookalike_limit():
    assert acronym_match("IBM", "International Business Machines")
    assert acronym_match("P&G", "The Procter & Gamble Company")
    assert not acronym_match("HP", "Hewlett Packard Enterprise")   # that's HPE
    assert not acronym_match("Microsoft", "Apple")


def test_domain_normalization():
    assert normalize_domain("https://www.IBM.com/us/en") == "ibm.com"
    assert normalize_domain("") == ""


def test_website_features():
    same = pair_features({"name": "IBM", "website": "ibm.com"}, {"name": "IBM Corp", "website": "www.ibm.com"})
    diff = pair_features({"name": "Amazon", "website": "amazon.com"}, {"name": "AWS", "website": "aws.amazon.com"})
    missing = pair_features({"name": "Amazon", "website": ""}, {"name": "AWS", "website": "aws.amazon.com"})
    assert same["website_same"] == 1 and same["website_diff"] == 0
    assert diff["website_same"] == 0 and diff["website_diff"] == 1
    assert missing["website_same"] == 0 and missing["website_diff"] == 0
