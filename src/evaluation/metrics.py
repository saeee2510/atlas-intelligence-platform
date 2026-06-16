def evaluate(preds, labels):

    tp = fp = fn = tn = 0

    for p, (_, _, l) in zip(preds, labels):

        if p == 1 and l == 1:
            tp += 1
        elif p == 1 and l == 0:
            fp += 1
        elif p == 0 and l == 1:
            fn += 1
        elif p == 0 and l == 0:
            tn += 1

    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    accuracy = (tp + tn) / (tp + tn + fp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)

    return {
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "f1": f1
    }