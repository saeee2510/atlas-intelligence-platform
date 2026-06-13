from src.entity_resolution.resolver import resolve
from src.evaluation.dataset import LABELS
from src.evaluation.metrics import evaluate


def run_evaluation():
    preds = []
    labels = []

    print("\n===== ENTITY RESOLUTION EVALUATION =====\n")

    for a_name, b_name, label in LABELS:

        a = {"name": a_name}
        b = {"name": b_name}

        result = resolve(a, b)

        # convert score → prediction
        pred = 1 if result["score"] > 0.60 else 0

        preds.append(pred)
        labels.append(label)

        print(
            f"{a_name:20} vs {b_name:20} "
            f"=> label={label} score={result['score']:.3f} pred={pred}"
        )

    metrics = evaluate(preds, labels)

    print("\n===== FINAL METRICS =====")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall:    {metrics['recall']:.3f}")
    print(f"F1 Score:  {metrics['f1']:.3f}")

    return metrics


if __name__ == "__main__":
    run_evaluation()