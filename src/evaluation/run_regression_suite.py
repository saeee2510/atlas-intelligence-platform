from src.evaluation.dataset import LABELS
from src.evaluation.metrics import evaluate
from src.evaluation.baseline import BASELINE_F1
from src.entity_resolution.resolver import resolve


def run_regression_suite():

    preds = []
    true_labels = []

    print("\n===== REGRESSION TEST SUITE =====\n")

    for a, b, label in LABELS:

        result = resolve(
            {"name": a},
            {"name": b}
        )

        pred = 1 if result["match"] else 0

        preds.append(pred)
        true_labels.append(label)

        print(
            f"{a:20} vs {b:20} => "
            f"score={result['score']:.4f} "
            f"pred={pred} label={label}"
        )

    # FIXED: correct evaluate call
    metrics = evaluate(preds, true_labels)

    f1 = metrics["f1"]

    print("\n===== RESULTS =====")
    print(f"F1: {f1:.3f}")
    print(f"Baseline F1: {BASELINE_F1:.3f}")

    if f1 < BASELINE_F1:
        print("\n REGRESSION DETECTED — TEST FAILED")
        exit(1)
    else:
        print("\n NO REGRESSION — TEST PASSED")
        exit(0)


if __name__ == "__main__":
    run_regression_suite()