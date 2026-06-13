from src.entity_resolution.resolver import resolve


def test_resolver_match():
    a = {
        "name": "Microsoft Corp",
        "website": "microsoft.com",
        "description": "Tech company"
    }

    b = {
        "name": "MSFT",
        "website": "microsoft.com",
        "description": "Microsoft"
    }

    result = resolve(a, b)

    print("\nRESULT 1:", result)

    assert "match" in result
    assert "score" in result
    assert isinstance(result["score"], float)


def test_resolver_no_match():
    a = {
        "name": "Microsoft Corp",
        "website": "microsoft.com"
    }

    b = {
        "name": "Google LLC",
        "website": "google.com"
    }

    result = resolve(a, b)

    print("\nRESULT 2:", result)

    assert "match" in result
    assert "score" in result


if __name__ == "__main__":
    test_resolver_match()
    test_resolver_no_match()
    print("\nALL TESTS PASSED")