from src.entity_resolution.fuzzy_match import fuzzy_score


def test_identical_strings():
    score = fuzzy_score("Microsoft Corp", "Microsoft Corp")
    assert score == 1.0


def test_word_order_invariance():
    score1 = fuzzy_score("Microsoft Corp", "Corp Microsoft")
    score2 = fuzzy_score("Corp Microsoft", "Microsoft Corp")

    assert score1 > 0.9
    assert score2 > 0.9
    assert abs(score1 - score2) < 0.05


def test_same_entity_different_variants():
    score = fuzzy_score("Microsoft Corp", "Microsoft Corporation")

    # should be strongly similar
    assert score > 0.75


def test_different_entities_low_similarity():
    score = fuzzy_score("Apple Inc", "Tesla Inc")

    # NOT assuming the exact value — just ensuring it's lower than same-entity match
    assert score < 0.8


def test_relative_similarity_logic():
    microsoft_pair = fuzzy_score("Microsoft Corp", "Microsoft Corporation")
    cross_pair = fuzzy_score("Microsoft Corp", "Tesla Inc")

    # key entity-resolution property:
    assert microsoft_pair > cross_pair


def test_noise_handling():
    score = fuzzy_score("Microsoft!!! Corp", "Microsoft Corp")
    assert score > 0.9


if __name__ == "__main__":
    test_identical_strings()
    test_word_order_invariance()
    test_same_entity_different_variants()
    test_different_entities_low_similarity()
    test_relative_similarity_logic()
    test_noise_handling()

    print("All fuzzy match tests passed!")