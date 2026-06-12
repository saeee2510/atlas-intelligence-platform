from src.processing.normalize import normalize_name

def test_normalization():
    assert normalize_name("Microsoft Corp") == "microsoft"
    assert normalize_name("Apple Inc.") == "apple"
    assert normalize_name("Tesla, Inc") == "tesla"
    assert normalize_name("Google LLC") == "google"

if __name__ == "__main__":
    test_normalization()
    print("All tests passed!")