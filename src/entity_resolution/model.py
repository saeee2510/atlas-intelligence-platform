"""
A small logistic regression that learns how to weight the pairwise features,
trained on the dev split only. Implemented with plain Python so it is fully
transparent and has no extra dependencies.
"""
import json
import math
from pathlib import Path

MODEL_FILE = Path("data/benchmark/model.json")


def _sigmoid(z):
    return 1 / (1 + math.exp(-max(min(z, 30), -30)))


def train(X, y, features, epochs=3000, lr=0.5, l2=0.01):
    """Batch gradient descent with L2 regularization. X: list of feature dicts."""
    w = {f: 0.0 for f in features}
    b = 0.0
    n = len(X)
    for _ in range(epochs):
        gw = {f: 0.0 for f in features}
        gb = 0.0
        for x, label in zip(X, y):
            err = _sigmoid(b + sum(w[f] * x[f] for f in features)) - label
            for f in features:
                gw[f] += err * x[f]
            gb += err
        for f in features:
            w[f] -= lr * (gw[f] / n + l2 * w[f])
        b -= lr * gb / n
    return {"features": features, "weights": w, "bias": b}


def predict_proba(model, x) -> float:
    return _sigmoid(model["bias"] + sum(model["weights"][f] * x[f] for f in model["features"]))


def save(model, path: Path = MODEL_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2))


def load(path: Path = MODEL_FILE):
    return json.loads(path.read_text()) if path.exists() else None
