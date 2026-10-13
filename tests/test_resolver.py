from src.entity_resolution import llm_judge, resolver

CONFIG = {"model": {"features": ["fuzzy", "compact_ratio", "acronym", "website_same", "website_diff", "embedding"],
                    "bias": -6.0, "weights": {"fuzzy": 4.0, "compact_ratio": 2.0, "acronym": 4.0,
                                              "website_same": 3.0, "website_diff": -4.0, "embedding": 3.0}},
          "band_low": 0.2, "band_high": 0.8, "threshold": 0.5, "use_llm": True}


def _with_fake_llm(verdict, fn):
    original = llm_judge.llm_match
    calls = []
    llm_judge.llm_match = lambda a, b: calls.append((a["name"], b["name"])) or verdict
    try:
        return fn(), calls
    finally:
        llm_judge.llm_match = original


def test_clear_match_skips_the_llm():
    result, calls = _with_fake_llm({}, lambda: resolver.resolve(
        {"name": "Microsoft Corp", "website": "microsoft.com"},
        {"name": "MICROSOFT CORPORATION", "website": "microsoft.com"}, config=CONFIG, embedding_sim=0.95))
    assert result["match"] and result["decision"] == "auto_match" and calls == []


def test_clear_non_match_skips_the_llm():
    result, calls = _with_fake_llm({}, lambda: resolver.resolve(
        {"name": "Tesla", "website": "tesla.com"}, {"name": "Oracle", "website": "oracle.com"},
        config=CONFIG, embedding_sim=0.2))
    assert not result["match"] and result["decision"] == "auto_reject" and calls == []


def test_uncertain_pair_goes_to_the_llm_and_low_confidence_is_flagged():
    verdict = {"match": True, "confidence": 0.6, "reason": "ticker"}
    result, calls = _with_fake_llm(verdict, lambda: resolver.resolve(
        {"name": "Microsoft", "website": ""}, {"name": "MSFT", "website": ""}, config=CONFIG, embedding_sim=0.7))
    assert calls == [("Microsoft", "MSFT")]
    assert result["match"] and result["used_llm"] and result["needs_review"]


def test_no_hardcoded_aliases():
    # the old resolver special-cased the exact benchmark pairs ("msft" -> "microsoft")
    assert not hasattr(resolver, "ALIASES")
