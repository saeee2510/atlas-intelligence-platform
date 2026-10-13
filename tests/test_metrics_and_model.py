from src.entity_resolution import model as scoring_model
from src.evaluation.metrics import accuracy_by_category, best_threshold, evaluate


def test_evaluate():
    m = evaluate([1, 1, 0, 0], [1, 0, 1, 0])
    assert (m["tp"], m["fp"], m["fn"], m["tn"]) == (1, 1, 1, 1)
    assert m["f1"] == 0.5


def test_evaluate_handles_no_positive_predictions():
    assert evaluate([0, 0], [1, 0])["precision"] == 0.0


def test_best_threshold_separates_classes():
    t = best_threshold([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1])
    assert 0.2 < t <= 0.8


def test_accuracy_by_category():
    rows = [{"category": "typo", "label": 1}, {"category": "typo", "label": 1}, {"category": "random", "label": 0}]
    assert accuracy_by_category(rows, [1, 0, 0]) == {"random": {"n": 1, "accuracy": 1.0},
                                                    "typo": {"n": 2, "accuracy": 0.5}}


def test_logistic_regression_learns_a_separable_feature():
    X = [{"f": 0.9}, {"f": 0.8}, {"f": 0.2}, {"f": 0.1}]
    m = scoring_model.train(X, [1, 1, 0, 0], ["f"], epochs=2000)
    assert m["weights"]["f"] > 0
    assert scoring_model.predict_proba(m, {"f": 0.95}) > 0.5 > scoring_model.predict_proba(m, {"f": 0.05})
