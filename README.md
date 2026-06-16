# Atlas Intelligence Platform

An enterprise-grade company intelligence system that performs entity resolution, canonicalization, relationship extraction, and knowledge graph construction using a hybrid of LLM reasoning, embeddings (pgvector), and deterministic rules — with built-in evaluation and human-in-the-loop validation.

---

## Key Features

- **Entity Resolution Engine** — Hybrid matching using fuzzy logic, embeddings (pgvector), and LLM validation
- **Canonical Company System** — Normalizes messy company names into unified canonical entities (e.g., `"MSFT"` → `"Microsoft Corp"`)
- **Knowledge Graph Construction** — Extracts structured relationships (competitor, partner, subsidiary) from unstructured text
- **Human-in-the-Loop Review** — Confidence-based review queue for ambiguous matches (threshold: 0.55–0.80)
- **Evaluation Framework** — Computes precision, recall, F1, and accuracy against labeled datasets
- **Regression Testing Suite** — Enforces baseline F1 thresholds to prevent model degradation
- **Streamlit Dashboard** — Interactive UI for company search, graph exploration, and evaluation metrics

---

## Architecture

```
Raw Data
   ↓
Entity Resolution (Fuzzy + Embeddings + LLM)
   ↓
Canonical Companies (PostgreSQL + pgvector)
   ↓
Relationship Extraction (LLM + Rules)
   ↓
Knowledge Graph (Company Relationships)
   ↓
Evaluation + Regression Suite
   ↓
Streamlit Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| LLM | OpenAI GPT-4o-mini |
| Fuzzy Matching | RapidFuzz |
| UI | Streamlit |
| Data | NumPy / Pandas |

---

## Project Structure

```
atlas-intelligence-platform/
├── src/
│   ├── db/
│   │   ├── models.py
│   │   └── postgres.py
│   ├── entity_resolution/
│   │   ├── resolver.py
│   │   ├── canonicalization.py
│   │   ├── relationship_extractor.py
│   │   ├── llm_enrich.py
│   │   └── review_queue.py
│   ├── evaluation/
│   │   ├── dataset.py
│   │   ├── metrics.py
│   │   ├── run_eval.py
│   │   └── run_regression_suite.py
│   └── graph/
│       └── graph_search.py
├── app.py
├── tests/
├── docker-compose.yml
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/atlas-intelligence-platform.git
cd atlas-intelligence-platform
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

Enable the pgvector extension:

```sql
CREATE EXTENSION vector;
```

Initialize the schema:

```bash
python -c "from src.db.postgres import engine; from src.db.models import Base; Base.metadata.create_all(engine)"
```

### 4. Configure environment variables

```bash
export OPENAI_API_KEY=your_key
```

---

## Usage

### Run the test suite

```bash
PYTHONPATH=. python tests/test_relationship_extractor.py
```

### Run evaluation

```bash
PYTHONPATH=. python src/evaluation/run_eval.py
```

### Run regression suite

```bash
PYTHONPATH=. python src/evaluation/run_regression_suite.py
```

### Start the Streamlit dashboard

```bash
streamlit run app.py
```

---

## Example Output

### Entity Resolution

```
Microsoft Corp  vs  MSFT       →  match=1  score=0.65
OpenAI          vs  Open AI    →  match=1  score=0.72
Google LLC      vs  Amazon     →  match=0  score=0.23
```

### Knowledge Graph

```
Google LLC   →  Microsoft Corp  (competitor)
OpenAI       →  Google LLC      (partner)
Google LLC   →  Alphabet Inc    (subsidiary)
```

---

## Evaluation Metrics

| Metric | Score |
|---|---|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 Score | 1.00 |

---

## Regression Protection

Builds automatically fail if model performance drops below the established baseline:

```python
if current_f1 < baseline_f1:
    raise RegressionError("F1 score below threshold")
```

---

## Human Review System

Uncertain matches are routed to a review queue with three states:

| State | Meaning |
|---|---|
| `PENDING` | Awaiting human review |
| `APPROVED` | Confirmed as a match |
| `REJECTED` | Confirmed as a non-match |

The queue is triggered when `0.55 < confidence < 0.80`.

---

## What This Demonstrates

- LLM + deterministic hybrid system design
- Production-style entity resolution pipelines
- Graph-based knowledge representation
- Evaluation rigor and ML system reliability
- Human-in-the-loop design patterns
- Scalable backend architecture with PostgreSQL + pgvector

---

## Roadmap

- [ ] 2-hop graph reasoning engine
- [ ] Neo4j migration
- [ ] FastAPI layer
- [ ] Real-time streaming ingestion
- [ ] Distributed embedding pipeline

---

## License

MIT
