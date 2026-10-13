"""
Regression gate: re-scores the held-out test split with the saved model and
fails (exit code 1) if F1 drops more than TOLERANCE below the saved baseline.

LLM verdicts come from the on-disk cache, so the gate is fast, deterministic,
and costs nothing unless the prompt or pairs change.

    python -m src.evaluation.run_regression_suite
"""
import sys

from src.entity_resolution import embedding_cache
from src.entity_resolution import model as scoring_model
from src.entity_resolution.resolver import resolve
from src.evaluation.baseline import TOLERANCE, load_baseline
from src.evaluation.build_benchmark import load
from src.evaluation.metrics import evaluate


def run_regression_suite() -> int:
    config = scoring_model.load()
    baseline = load_baseline()
    if not config or not baseline:
        print("No trained model or baseline. Run: python -m src.evaluation.run_ablation --set-baseline")
        return 1

    test = [r for r in load() if r["split"] == "test"]
    vectors = embedding_cache.embed_many(sorted({r["a_name"] for r in test} | {r["b_name"] for r in test}))
    preds = []
    for r in test:
        a = {"name": r["a_name"], "website": r["a_website"]}
        b = {"name": r["b_name"], "website": r["b_website"]}
        sim = embedding_cache.cosine(vectors.get(a["name"]), vectors.get(b["name"]))
        preds.append(int(resolve(a, b, config=config, embedding_sim=sim)["match"]))

    f1 = evaluate(preds, [r["label"] for r in test])["f1"]
    print(f"Test F1: {f1:.4f} | baseline: {baseline['f1']:.4f} | tolerance: {TOLERANCE}")
    if f1 < baseline["f1"] - TOLERANCE:
        print("REGRESSION DETECTED: failing build")
        return 1
    print("No regression")
    return 0


if __name__ == "__main__":
    sys.exit(run_regression_suite())
