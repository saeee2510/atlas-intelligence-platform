from src.entity_resolution.blocking import blocking_key


def test_same_prefix():
    assert blocking_key("Microsoft") == blocking_key("Microsoft Corp")


def test_different_prefix():
    assert blocking_key("Microsoft") != blocking_key("Google LLC")


def test_short_name():
    assert blocking_key("AI") == "ai"


if __name__ == "__main__":
    test_same_prefix()
    test_different_prefix()
    test_short_name()
    print("All tests passed!")