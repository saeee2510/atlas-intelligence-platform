"""The regression suite fails if test F1 drops below the saved baseline."""
import json
from pathlib import Path

BASELINE_FILE = Path("data/benchmark/baseline.json")
TOLERANCE = 0.01  # allow tiny run-to-run noise


def load_baseline():
    return json.loads(BASELINE_FILE.read_text()) if BASELINE_FILE.exists() else None


def save_baseline(metrics: dict):
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(metrics, indent=2))
