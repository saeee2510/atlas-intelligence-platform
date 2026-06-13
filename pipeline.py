import pandas as pd
from src.processing.normalize import normalize_name
from src.entity_resolution.resolver import resolve


def run_pipeline():
    # 1. Load data ONCE
    df = pd.read_csv("data/raw/companies.csv")

    # 2. Normalize ONCE
    df["normalized"] = df["name"].apply(normalize_name)

    print("\n===== DATA =====")
    print(df)

    # 3. Define pairs ONCE
    pairs = [
        (df.iloc[0], df.iloc[1]),
        (df.iloc[3], df.iloc[4]),
    ]

    print("\n===== RESOLUTION RESULTS =====")

    # 4. Run resolver ONCE
    for a, b in pairs:
        entity_a = {
            "name": a["normalized"],
            "website": a.get("website", None)
        }

        entity_b = {
            "name": b["normalized"],
            "website": b.get("website", None)
        }

        result = resolve(entity_a, entity_b)

        print(
            f"{a['name']}  vs  {b['name']}  "
            f"=> score={result['score']} match={result['match']}"
        )


# 5. ENTRY POINT (IMPORTANT)
if __name__ == "__main__":
    run_pipeline()