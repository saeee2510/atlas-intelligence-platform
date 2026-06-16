from src.entity_resolution.resolver import resolve
from src.evaluation.dataset import LABELS
from src.evaluation.metrics import evaluate


def run_eval():

    preds = []

    print("\n===== ENTITY RESOLUTION EVALUATION =====\n")

    for a, b, label in LABELS:

        result = resolve(
            {"name": a},
            {"name": b}
        )

        pred = 1 if result["match"] else 0
        preds.append(pred)

        print(
            f"{a:20} vs {b:20} => "
            f"label={label} score={result['score']} pred={pred}"
        )

    metrics = evaluate(preds, LABELS)

    print("\n===== FINAL METRICS =====")
    for k, v in metrics.items():
        print(f"{k.capitalize()}: {v:.3f}")


if __name__ == "__main__":
    run_eval()