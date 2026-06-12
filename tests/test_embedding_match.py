from src.entity_resolution.embedding_match import embedding_score


def test_same_entity_high_similarity():
    score = embedding_score("Microsoft Corp", "Microsoft Corporation")
    assert score > 0.8


def test_simple_alias():
    apple = embedding_score("Apple Inc", "Apple")
    tesla = embedding_score("Apple Inc", "Tesla Inc")

    assert apple > tesla


def test_unrelated_low_similarity():
    score = embedding_score("Apple Inc", "Tesla Inc")
    assert score < 0.7


def test_relative_ranking():
    same = embedding_score("Microsoft Corp", "Microsoft Corporation")
    different = embedding_score("Microsoft Corp", "Tesla Inc")


    assert same > different


if __name__ == "__main__":
    test_same_entity_high_similarity()
    test_simple_alias()
    test_unrelated_low_similarity()
    test_relative_ranking()

    print("All embedding tests passed!")