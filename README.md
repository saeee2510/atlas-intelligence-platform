# Atlas: Company Entity Resolution & Knowledge Graph Platform

Atlas decides whether messy company records refer to the same company ("IBM" vs "International Business Machines Corporation", "MSFT" vs "Microsoft", "Facebook, Inc." vs "Meta Platforms"), merges them into canonical companies, and links canonical companies in a knowledge graph of competitor, partner, and subsidiary relationships.

The resolver is a hybrid: cheap signals decide the easy pairs, and an LLM judge is called only for the pairs the model is unsure about.

## Results

Measured on a 461-pair labeled benchmark of real companies (`data/benchmark/pairs.csv`), trained and tuned on 224 dev pairs and reported on 237 held-out test pairs:

| Configuration | Precision | Recall | F1 | LLM calls |
| --- | --- | --- | --- | --- |
| Fuzzy matching only | 0.910 | 0.864 | 0.886 | 0 |
| + acronym, compact-name & website rules | 0.915 | 0.921 | 0.918 | 0 |
| + embeddings (learned weights) | 0.917 | 0.943 | 0.930 | 0 |
| **+ LLM judge on uncertain pairs (final)** | **0.936** | **0.943** | **0.940** | **8** |
| LLM judge on every pair | 0.991 | 0.757 | 0.858 | 237 |

- Every stage adds accuracy: **0.886 → 0.940 F1**.
- The hybrid **beats LLM-only matching by 8 F1 points while sending only 3.4% of pairs to the LLM** (8 of 237). The LLM alone is very precise but misses a quarter of true matches, mostly tickers and abbreviations it treats as uncertain.
- **Wider LLM bands made results worse** on dev (F1 0.946 → 0.835 as the band grew from 37 to 197 LLM calls): the learned model is more accurate than the LLM on pairs it is confident about. The band is therefore chosen to be the cheapest one within 0.01 dev F1 of the best.

### Blocking

Canonicalization compares only records that share a blocking key instead of all pairs:

| Strategy | Comparisons | Reduction | True matches kept |
| --- | --- | --- | --- |
| Rule keys | 447 of 39,340 | 98.9% | 83.2% |
| Rule keys + 3 nearest embedding neighbors | 663 of 39,340 | **98.3%** | **93.1%** |

Embedding neighbors recover tickers and renames ("MSFT", "Facebook") that share no characters with the canonical name.

Per-category accuracy and the remaining test errors are in [`evaluation/report.md`](evaluation/report.md).

## The benchmark

`src/evaluation/build_benchmark.py` deterministically builds the labeled pairs from a curated list of 66 real companies.

| Matches (label 1) | Non-matches (label 0) |
| --- | --- |
| format variants ("MICROSOFT CORP." vs "Microsoft Corporation") | subsidiaries ("Amazon" vs "Amazon Web Services", "Microsoft" vs "LinkedIn") |
| acronyms ("IBM", "P&G", "BofA") | lookalikes ("HP Inc." vs "Hewlett Packard Enterprise", "GE" vs "GM" vs "General Mills", "Square, Inc." vs "Square Enix") |
| stock tickers ("MSFT", "KO") | competitors ("Visa" vs "Mastercard") |
| typos ("Netfilx") | random unrelated pairs |
| renames ("Facebook, Inc." vs "Meta Platforms") | |

- Websites are removed from one or both records in many pairs, so a website match can't solve the benchmark on its own.
- The dev/test split is **by entity**, not by pair, so names used for training and threshold tuning don't appear in the test set.

An earlier version of this project reported F1 1.00 on 5 pairs. That score came from a hardcoded alias table that matched the exact test cases; the table has been removed, and a test now guards against it.

## How the resolver works

```
record A, record B
   │
   ├─ features ─ fuzzy        token-set similarity of normalized names
   │             compact      similarity with spaces removed ("Open AI" vs "OpenAI")
   │             acronym      one name is an initialism of the other
   │             website      same domain / different domains (strong negative)
   │             embedding    cosine similarity of name embeddings
   │
   ├─ learned logistic score p(match)   (weights trained on dev only)
   │
   ├─ p ≥ 0.6  → match       (no LLM)
   ├─ p ≤ 0.4  → no match    (no LLM)
   └─ between  → GPT-4o-mini judge decides; low-confidence answers go to the human review queue
```

- **Normalization** strips legal suffixes (Inc, Corp, LLC, plc, Holdings…), punctuation, and leading "The", and maps "&" to "and".
- **The LLM judge** has explicit rules: renames are the same entity, parents and subsidiaries are not. Verdicts are cached on disk by prompt version, model, and pair, so evaluations are reproducible and re-runs are free.
- **The resolver has no side effects.** Canonicalization decides what to store, and writes low-confidence pairs to the review queue.

## Pipeline

```
companies (raw records + cached embeddings in pgvector)
   → blocking (shared keys + nearest embedding neighbors)
   → resolver (rules + embeddings + LLM on uncertain pairs)
   → canonical companies + mappings  (uncertain pairs → review queue)
   → LLM enrichment (industry, business model, size)
   → relationship extraction from text → knowledge graph
   → Streamlit dashboard (search, review queue, evaluation, graph)
```

## Regression gate

```bash
python -m src.evaluation.run_regression_suite
```

Re-scores the test split with the saved model and exits with code 1 if F1 drops more than 0.01 below the saved baseline (`data/benchmark/baseline.json`). It uses cached LLM verdicts, so it is deterministic and costs nothing unless the prompt or the pairs change.

## Tech stack

Python · PostgreSQL · pgvector · SQLAlchemy · RapidFuzz · OpenAI (GPT-4o-mini, text-embedding-3-small) · Streamlit · Docker

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # add your OPENAI_API_KEY
```

### Run the evaluation (no database needed)

```bash
python -m src.evaluation.run_ablation --set-baseline   # ~5 minutes and ~$0.05 the first time; cached afterwards
python -m src.evaluation.run_regression_suite
python -m pytest tests
```

### Run the full pipeline

```bash
docker compose up -d                                  # Postgres + pgvector on port 5451
python -m scripts.init_db
python -m src.ingestion.load_companies --benchmark    # ~280 company records with embeddings
python pipeline.py                                    # blocking + resolution + canonicalization
python -m scripts.inspect_db                          # canonical companies, mappings, review queue
streamlit run app.py
```

## Project structure

```
app.py                       Streamlit dashboard
pipeline.py                  canonicalization entry point
data/benchmark/              pairs.csv, trained model.json, baseline.json
src/processing/              normalize.py, features.py
src/entity_resolution/       resolver, model (logistic regression), blocking, llm_judge,
                             embedding_cache, canonicalization, relationship_extractor,
                             graph_search, vector_search, review_queue
src/evaluation/              build_benchmark, run_ablation, run_regression_suite, metrics
src/ingestion/               load_companies
scripts/                     init_db, inspect_db, relationship_demo
tests/                       26 offline tests (no API key or database needed)
```

## Limitations

- The benchmark is hand-curated: real companies, but generated name variants and a modest size (461 pairs). A larger, independently labeled dataset would give tighter error bars.
- Acronyms can collide: "GM" is an initialism of both General Motors and General Mills.
- The LLM judge is conservative ("if unsure, answer false"), which keeps precision high but limits its recall on tickers.
- Relationship extraction is not yet evaluated against labeled relationships, and the parent-company map is a small hand-written list.
