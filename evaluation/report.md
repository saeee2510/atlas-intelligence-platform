# Atlas Entity Resolution: Evaluation

Run 2026-10-12T19:09:36 · 461 labeled pairs (224 dev for training/tuning, 237 held-out test)

## Ablation (test split)

| Configuration | Precision | Recall | F1 | LLM calls |
| --- | --- | --- | --- | --- |
| Fuzzy only | 0.910 | 0.864 | **0.886** | 0 |
| + acronym, compact & website rules | 0.915 | 0.921 | **0.918** | 0 |
| + embeddings (learned weights) | 0.917 | 0.943 | **0.930** | 0 |
| + LLM judge on uncertain band (final) | 0.936 | 0.943 | **0.940** | 8 |
| LLM judge on every pair | 0.991 | 0.757 | **0.858** | 237 |

Final configuration sends 3% of pairs to the LLM (band 0.4–0.6), costing $0.0003 for 237 pairs.
LLM-on-everything costs $0.0096 for F1 0.858.

## Accuracy by pair type (test)

| Category | Pairs | Fuzzy only | Final |
| --- | --- | --- | --- |
| acronym | 10 | 0.40 | 1.00 |
| competitor | 14 | 0.86 | 1.00 |
| format | 81 | 0.95 | 0.97 |
| lookalike | 9 | 0.22 | 0.22 |
| random | 62 | 0.98 | 1.00 |
| subsidiary | 12 | 0.83 | 0.83 |
| ticker | 18 | 0.50 | 0.67 |
| typo | 31 | 1.00 | 1.00 |

## Blocking

| Strategy | Comparisons | Reduction | True matches kept |
| --- | --- | --- | --- |
| Rule keys | 447 of 39340 | 98.9% | 83.2% |
| Rule keys + 3 embedding neighbors | 663 of 39340 | 98.3% | 93.1% |

## Remaining test errors (17)

- [ticker] Alphabet Inc. vs GOOGL: expected match, got auto_reject (score 0.2052)
- [format] International Business Machines Corporation vs IBM Corp: expected match, got auto_reject (score 0.3376)
- [format] IBM Corp vs International Business Machines: expected match, got auto_reject (score 0.3219)
- [ticker] Salesforce, Inc. vs CRM: expected match, got auto_reject (score 0.214)
- [ticker] American Airlines Group Inc. vs AAL: expected match, got auto_reject (score 0.3564)
- [ticker] American Express Company vs AXP: expected match, got auto_reject (score 0.3257)
- [ticker] Bank of America Corporation vs BAC: expected match, got auto_reject (score 0.2755)
- [ticker] Teradata Corporation vs TDC: expected match, got auto_reject (score 0.3764)
- [subsidiary] Amazon Inc vs Amazon Web Services, Inc.: expected non-match, got auto_match (score 0.8336)
- [subsidiary] Amazon vs Amazon Web Services, Inc.: expected non-match, got auto_match (score 0.7742)
- [lookalike] GM vs General Mills, Inc.: expected non-match, got auto_match (score 0.6417)
- [lookalike] General Motors Company vs General Mills, Inc.: expected non-match, got auto_match (score 0.7445)
- [lookalike] American Airlines Group Inc. vs American Express: expected non-match, got auto_match (score 0.717)
- [lookalike] JPMorgan Chase & Co. vs Morgan Stanley & Co.: expected non-match, got auto_match (score 0.7182)
- [lookalike] JP Morgan Chase & Co vs Morgan Stanley & Co.: expected non-match, got auto_match (score 0.782)
- [lookalike] Target vs Target Hospitality Corp.: expected non-match, got auto_match (score 0.7163)
- [lookalike] Target vs Target Hospitality: expected non-match, got auto_match (score 0.741)
