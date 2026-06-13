from src.entity_resolution.resolver import resolve
from src.evaluation.dataset import LABELS
from src.evaluation.metrics import precision, recall, f1


def run_evaluation(threshold=0.75):
    tp = fp = fn = tn = 0

    results = []

    for entity_a, entity_b, label in LABELS:
        output = resolve(entity_a, entity_b)

        score = output["score"]
        pred = score >= threshold

        # confusion matrix update
        if pred and label == 1:
            tp += 1
        elif pred and label == 0:
            fp += 1
        elif not pred and label == 1:
            fn += 1
        else:
            tn += 1

        results.append({
            "entity_a": entity_a,
            "entity_b": entity_b,
            "label": label,
            "score": score,
            "pred": pred
        })

    # compute metrics
    p = precision(tp, fp)
    r = recall(tp, fn)
    f = f1(p, r)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(p, 3),
        "recall": round(r, 3),
        "f1": round(f, 3),
        "results": results
    }


if __name__ == "__main__":
    report = run_evaluation()

    print("\n===== ENTITY RESOLUTION EVALUATION =====\n")

    print(f"TP: {report['tp']}")
    print(f"FP: {report['fp']}")
    print(f"FN: {report['fn']}")
    print(f"TN: {report['tn']}\n")

    print(f"Precision: {report['precision']}")
    print(f"Recall:    {report['recall']}")
    print(f"F1 Score:  {report['f1']}\n")

    print("===== SAMPLE RESULTS =====")
    for r in report["results"]:
        print(
            f"{r['entity_a']}  vs  {r['entity_b']}  "
            f"=> label={r['label']} score={r['score']} pred={r['pred']}"
        )