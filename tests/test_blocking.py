from src.entity_resolution.blocking import blocking_keys, candidate_pairs, evaluate_blocking


def test_variants_share_a_key():
    assert blocking_keys({"name": "Microsoft"}) & blocking_keys({"name": "MICROSOFT CORP."})
    assert blocking_keys({"name": "Open AI"}) & blocking_keys({"name": "OpenAI"})
    assert blocking_keys({"name": "IBM"}) & blocking_keys({"name": "International Business Machines"})


def test_unrelated_names_do_not_share_keys():
    assert not blocking_keys({"name": "Microsoft"}) & blocking_keys({"name": "Tesla, Inc."})


def test_embedding_neighbors_add_candidates():
    records = [{"name": "Microsoft"}, {"name": "MSFT"}, {"name": "Tesla"}]
    embeddings = {"Microsoft": [1.0, 0.0], "MSFT": [0.95, 0.05], "Tesla": [0.0, 1.0]}
    assert (0, 1) not in candidate_pairs(records)
    assert (0, 1) in candidate_pairs(records, embeddings, k_neighbors=1)


def test_evaluate_blocking_reports_completeness_and_reduction():
    pairs = [{"a_name": "Microsoft", "b_name": "Microsoft Corp", "label": 1},
             {"a_name": "Microsoft", "b_name": "MSFT", "label": 1},
             {"a_name": "Tesla", "b_name": "Apple", "label": 0}]
    m = evaluate_blocking(pairs)
    assert m["pair_completeness"] == 0.5          # the ticker pair is missed by rule keys
    assert 0 < m["reduction_ratio"] < 1
