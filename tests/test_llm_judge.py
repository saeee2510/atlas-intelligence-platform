from src.entity_resolution.llm_judge import llm_match


def test_llm():
    a = {
        "name": "Microsoft Corp",
        "website": "microsoft.com",
        "description": "Technology company"
    }

    b = {
        "name": "MSFT",
        "website": "microsoft.com",
        "description": "Microsoft company"
    }

    result = llm_match(a, b)

    print("LLM Output:", result)

    # Basic sanity check (string JSON)
    assert "match" in result
    assert "confidence" in result


if __name__ == "__main__":
    test_llm()