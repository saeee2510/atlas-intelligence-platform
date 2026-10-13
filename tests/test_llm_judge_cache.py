from src.entity_resolution import llm_judge


def test_cache_key_is_order_independent():
    a, b = {"name": "IBM", "website": "ibm.com"}, {"name": "International Business Machines"}
    assert llm_judge._key(a, b) == llm_judge._key(b, a)


def test_cached_verdicts_do_not_call_the_api():
    a, b = {"name": "X Corp"}, {"name": "X Corporation"}
    original = llm_judge._cache
    llm_judge._cache = {llm_judge._key(a, b): {"match": True, "confidence": 0.9, "reason": "cached"}}
    try:
        before = llm_judge.calls_made
        result = llm_judge.llm_match(a, b)
        assert result["match"] and result["cached"] and llm_judge.calls_made == before
    finally:
        llm_judge._cache = original
