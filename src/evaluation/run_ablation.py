"""
Ablation study: what does each stage of the resolver contribute?

Configurations (each tuned on the dev split, reported on the held-out test split):
  1. fuzzy_only    token-set fuzzy score with a tuned threshold
  2. rules         + compact match, acronym rule, website signals (learned weights)
  3. hybrid        + embedding similarity (learned weights)
  4. hybrid_llm    + LLM judge only for pairs in the uncertain score band  <- final
                   (band = fewest LLM calls within 0.01 dev F1 of the best band)
  5. llm_only      LLM judge on every pair (accuracy/cost reference point)

Also measures blocking: how many comparisons are avoided, and how many true
matches survive blocking.

Usage:
    python -m src.evaluation.run_ablation                 # full study
    python -m src.evaluation.run_ablation --skip-llm-only # cheaper, no LLM-on-everything run
    python -m src.evaluation.run_ablation --set-baseline  # also save final test F1 as the baseline
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from src.entity_resolution import embedding_cache, llm_judge
from src.entity_resolution import model as scoring_model
from src.entity_resolution.blocking import evaluate_blocking
from src.entity_resolution.resolver import resolve
from src.evaluation.baseline import save_baseline
from src.evaluation.build_benchmark import OUT as BENCHMARK, build, load, write
from src.evaluation.metrics import accuracy_by_category, best_threshold, evaluate
from src.processing.features import ALL_FEATURES, RULE_FEATURES, pair_features

RESULTS_DIR = Path("evaluation/results")
REPORT = Path("evaluation/report.md")
BANDS = [(0.4, 0.6), (0.3, 0.7), (0.2, 0.8), (0.1, 0.9), (0.05, 0.95)]
F1_SLACK = 0.01
PRICE_IN, PRICE_OUT = 0.15 / 1e6, 0.60 / 1e6   # gpt-4o-mini, USD per token


def records(row):
    return ({"name": row["a_name"], "website": row["a_website"]},
            {"name": row["b_name"], "website": row["b_website"]})


def llm_stats(verdicts):
    fresh = [v for v in verdicts if v.get("latency_ms") is not None]
    return {
        "llm_calls": len(verdicts),
        "avg_llm_latency_ms": round(sum(v["latency_ms"] for v in fresh) / len(fresh), 1) if fresh else None,
        "llm_cost_usd": round(sum(v.get("tokens_in", 0) * PRICE_IN + v.get("tokens_out", 0) * PRICE_OUT
                                  for v in verdicts), 5),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-llm-only", action="store_true")
    parser.add_argument("--set-baseline", action="store_true")
    args = parser.parse_args()

    if not BENCHMARK.exists():
        write(build())
    rows = load()
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]
    print(f"Benchmark: {len(rows)} pairs ({len(dev)} dev / {len(test)} test)")

    # one embedding call per unique name, cached on disk
    names = sorted({r["a_name"] for r in rows} | {r["b_name"] for r in rows})
    vectors = embedding_cache.embed_many(names)
    for r in rows:
        a, b = records(r)
        sim = embedding_cache.cosine(vectors.get(a["name"]), vectors.get(b["name"]))
        r["features"] = pair_features(a, b, sim)

    y_dev, y_test = [r["label"] for r in dev], [r["label"] for r in test]
    results = {}

    # 1. fuzzy only
    t = best_threshold([r["features"]["fuzzy"] for r in dev], y_dev)
    preds = [int(r["features"]["fuzzy"] >= t) for r in test]
    results["fuzzy_only"] = {**evaluate(preds, y_test), "threshold": t, "llm_calls": 0}
    fuzzy_preds = preds

    # 2 + 3. learned combinations
    trained = {}
    for name, feats in (("rules", RULE_FEATURES), ("hybrid", ALL_FEATURES)):
        m = scoring_model.train([r["features"] for r in dev], y_dev, feats)
        dev_scores = [scoring_model.predict_proba(m, r["features"]) for r in dev]
        t = best_threshold(dev_scores, y_dev)
        preds = [int(scoring_model.predict_proba(m, r["features"]) >= t) for r in test]
        results[name] = {**evaluate(preds, y_test), "threshold": t, "llm_calls": 0,
                         "weights": {k: round(v, 3) for k, v in m["weights"].items()},
                         "bias": round(m["bias"], 3)}
        trained[name] = (m, t)

    # 4. hybrid + LLM band, band chosen on dev (best F1, then fewest LLM calls)
    hybrid_model, hybrid_t = trained["hybrid"]
    band_scores = []
    for low, high in BANDS:
        cfg = {"model": hybrid_model, "band_low": low, "band_high": high, "threshold": hybrid_t, "use_llm": True}
        out = [resolve(*records(r), config=cfg, embedding_sim=r["features"]["embedding"]) for r in dev]
        f1 = evaluate([int(o["match"]) for o in out], y_dev)["f1"]
        band_scores.append((f1, -sum(o["used_llm"] for o in out), low, high))
        print(f"  dev band ({low}, {high}): F1 {f1:.3f}, LLM calls {sum(o['used_llm'] for o in out)}")
    # cost-aware choice: the fewest LLM calls among bands within F1_SLACK of the best dev F1
    best_f1 = max(f1 for f1, *_ in band_scores)
    _, _, low, high = max((b for b in band_scores if b[0] >= best_f1 - F1_SLACK), key=lambda b: b[1])
    final_cfg = {"model": hybrid_model, "band_low": low, "band_high": high,
                 "threshold": hybrid_t, "use_llm": True}

    start = time.perf_counter()
    out = [resolve(*records(r), config=final_cfg, embedding_sim=r["features"]["embedding"]) for r in test]
    final_preds = [int(o["match"]) for o in out]
    llm_out = [llm_judge.llm_match(*records(r)) for r, o in zip(test, out) if o["used_llm"]]
    results["hybrid_llm"] = {**evaluate(final_preds, y_test), "band": [low, high],
                             **llm_stats(llm_out),
                             "llm_call_rate": round(len(llm_out) / len(test), 3),
                             "needs_review": sum(o["needs_review"] for o in out),
                             "wall_time_s": round(time.perf_counter() - start, 2)}

    # 5. LLM on everything
    if not args.skip_llm_only:
        all_llm = [llm_judge.llm_match(*records(r)) for r in test]
        results["llm_only"] = {**evaluate([int(v["match"]) for v in all_llm], y_test), **llm_stats(all_llm),
                               "llm_call_rate": 1.0}
    llm_judge.save_cache()

    # blocking
    blocking = {"rules_only": evaluate_blocking(rows),
                "rules_plus_embedding_neighbors": evaluate_blocking(rows, vectors, k_neighbors=3)}

    by_category = {"fuzzy_only": accuracy_by_category(test, fuzzy_preds),
                   "hybrid_llm": accuracy_by_category(test, final_preds)}
    errors = [{"category": r["category"], "a": r["a_name"], "b": r["b_name"], "label": r["label"],
               "decision": o["decision"], "score": o["score"], "reason": o.get("reason", "")}
              for r, o in zip(test, out) if int(o["match"]) != r["label"]]

    scoring_model.save(final_cfg)
    summary = {"run": datetime.now().isoformat(timespec="seconds"),
               "benchmark": {"pairs": len(rows), "dev": len(dev), "test": len(test),
                             "matches": sum(r["label"] for r in rows)},
               "results": results, "blocking": blocking, "accuracy_by_category": by_category,
               "test_errors": errors}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"ablation_{datetime.now():%Y%m%d_%H%M%S}.json"
    out_path.write_text(json.dumps(summary, indent=2))
    write_report(summary)
    if args.set_baseline:
        save_baseline({"f1": results["hybrid_llm"]["f1"], "run": summary["run"]})

    print(json.dumps({k: {m: v.get(m) for m in ("precision", "recall", "f1", "llm_calls")}
                      for k, v in results.items()}, indent=2))
    print(json.dumps(blocking, indent=2))
    print(f"\nSaved {out_path}, {REPORT}, and {scoring_model.MODEL_FILE}")


def write_report(s):
    r, b = s["results"], s["blocking"]
    labels = {"fuzzy_only": "Fuzzy only", "rules": "+ acronym, compact & website rules",
              "hybrid": "+ embeddings (learned weights)", "hybrid_llm": "+ LLM judge on uncertain band (final)",
              "llm_only": "LLM judge on every pair"}
    lines = ["# Atlas Entity Resolution: Evaluation", "",
             f"Run {s['run']} · {s['benchmark']['pairs']} labeled pairs "
             f"({s['benchmark']['dev']} dev for training/tuning, {s['benchmark']['test']} held-out test)", "",
             "## Ablation (test split)", "",
             "| Configuration | Precision | Recall | F1 | LLM calls |", "| --- | --- | --- | --- | --- |"]
    for k, label in labels.items():
        if k in r:
            lines.append(f"| {label} | {r[k]['precision']:.3f} | {r[k]['recall']:.3f} | "
                         f"**{r[k]['f1']:.3f}** | {r[k].get('llm_calls', 0)} |")
    final = r["hybrid_llm"]
    lines += ["", f"Final configuration sends {final['llm_call_rate'] * 100:.0f}% of pairs to the LLM "
                  f"(band {final['band'][0]}–{final['band'][1]}), costing ${final['llm_cost_usd']:.4f} "
                  f"for {s['benchmark']['test']} pairs."]
    if "llm_only" in r:
        lo = r["llm_only"]
        lines.append(f"LLM-on-everything costs ${lo['llm_cost_usd']:.4f} for F1 {lo['f1']:.3f}.")
    lines += ["", "## Accuracy by pair type (test)", "", "| Category | Pairs | Fuzzy only | Final |",
              "| --- | --- | --- | --- |"]
    for cat, v in s["accuracy_by_category"]["hybrid_llm"].items():
        fz = s["accuracy_by_category"]["fuzzy_only"][cat]["accuracy"]
        lines.append(f"| {cat} | {v['n']} | {fz:.2f} | {v['accuracy']:.2f} |")
    lines += ["", "## Blocking", "", "| Strategy | Comparisons | Reduction | True matches kept |",
              "| --- | --- | --- | --- |"]
    for k, label in (("rules_only", "Rule keys"), ("rules_plus_embedding_neighbors", "Rule keys + 3 embedding neighbors")):
        lines.append(f"| {label} | {b[k]['candidate_pairs']} of {b[k]['all_pairs']} | "
                     f"{b[k]['reduction_ratio'] * 100:.1f}% | {b[k]['pair_completeness'] * 100:.1f}% |")
    lines += ["", f"## Remaining test errors ({len(s['test_errors'])})", ""]
    for e in s["test_errors"]:
        expected = "match" if e["label"] else "non-match"
        lines.append(f"- [{e['category']}] {e['a']} vs {e['b']}: expected {expected}, "
                     f"got {e['decision']} (score {e['score']})")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
