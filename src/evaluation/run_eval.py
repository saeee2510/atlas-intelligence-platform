from src.entity_resolution.resolver import resolve
from src.evaluation.dataset import LABELS
from src.evaluation.metrics import evaluate


def run_eval():

    preds = []
    true_labels = []

    print("\n===== ENTITY RESOLUTION EVALUATION =====\n")

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
            f"label={label} "
            f"score={result['score']:.4f} "
            f"pred={pred}"
        )

    metrics = evaluate(preds, true_labels)

    print("\n===== FINAL METRICS =====")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall: {metrics['recall']:.3f}")
    print(f"Accuracy: {metrics['accuracy']:.3f}")
    print(f"F1: {metrics['f1']:.3f}")

    # IMPORTANT: return metrics for Streamlit
    return metrics


if __name__ == "__main__":
    run_eval()