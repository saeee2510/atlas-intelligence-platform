"""Latest evaluation results, for the dashboard. Run run_ablation.py to refresh them."""
import glob
import json


def latest_results():
    files = sorted(glob.glob("evaluation/results/ablation_*.json"))
    return json.loads(open(files[-1]).read()) if files else None


def run_eval():
    """Final-configuration test metrics (kept for the existing dashboard)."""
    s = latest_results()
    return s["results"]["hybrid_llm"] if s else None


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2))
