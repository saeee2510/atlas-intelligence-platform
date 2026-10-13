def evaluate(preds, labels):
    tp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 0)
    fn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 1)
    tn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "accuracy": round(accuracy, 4), "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def best_threshold(scores, labels, grid=None):
    """Threshold that maximizes F1 (ties -> higher threshold, i.e. fewer false matches)."""
    grid = grid or [i / 100 for i in range(5, 96)]
    best = max(grid, key=lambda t: (evaluate([int(s >= t) for s in scores], labels)["f1"], t))
    return best


def accuracy_by_category(rows, preds):
    out = {}
    for cat in sorted({r["category"] for r in rows}):
        idx = [i for i, r in enumerate(rows) if r["category"] == cat]
        out[cat] = {"n": len(idx),
                    "accuracy": round(sum(preds[i] == rows[i]["label"] for i in idx) / len(idx), 3)}
    return out
