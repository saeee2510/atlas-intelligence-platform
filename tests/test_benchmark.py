from collections import Counter

from src.evaluation.build_benchmark import build


def test_build_is_deterministic():
    assert build() == build()


def test_benchmark_shape():
    rows = build()
    labels = Counter(r["label"] for r in rows)
    assert len(rows) > 400 and labels[0] > 150 and labels[1] > 200
    assert {"dev", "test"} == {r["split"] for r in rows}


def test_no_duplicate_pairs():
    keys = [tuple(sorted([r["a_name"].lower(), r["b_name"].lower()])) for r in build()]
    assert len(keys) == len(set(keys))


def test_split_is_by_entity_group():
    rows = build()
    for g in {r["group"] for r in rows}:
        assert len({r["split"] for r in rows if r["group"] == g}) == 1


def test_hard_labels_are_correct():
    labels = {(r["a_name"], r["b_name"]): r["label"] for r in build()}
    def label(a, b):
        return labels.get((a, b), labels.get((b, a)))
    assert label("Meta Platforms, Inc.", "Facebook, Inc.") == 1          # rename = same entity
    assert label("HP Inc.", "Hewlett Packard Enterprise Company") == 0   # spin-off = different
    assert label("Alphabet Inc.", "Google LLC") == 0                     # parent vs subsidiary
