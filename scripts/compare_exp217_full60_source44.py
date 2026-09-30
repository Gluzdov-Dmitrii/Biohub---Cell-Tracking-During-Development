"""Compare EXP217 full60 source44 candidate against EXP214 gapfix90 baseline."""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from compare_exp214_results import arrays, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metrics = json.loads(args.metrics.read_text())
    assert metrics["status"] == "PASS_HONEST_PAIRED_CV"
    expected = {
        "baseline_gapfix90_public",
        "candidate_full60_source44_public",
        "baseline_gapfix90_local",
        "candidate_full60_source44_local",
    }
    assert set(metrics["rows"]) == expected
    rows = {name: sorted(values, key=lambda row: row["dataset"]) for name, values in metrics["rows"].items()}
    names = [row["dataset"] for row in next(iter(rows.values()))]
    assert len(names) == 175
    assert all([row["dataset"] for row in values] == names for values in rows.values())
    data = {name: arrays(values) for name, values in rows.items()}
    for name, summary in metrics["summary"].items():
        assert abs(float(score(data[name])) - summary["score"]) < 1e-12
    groups = [np.array([i for i, name in enumerate(names) if name.startswith(prefix + "_")]) for prefix in ("44b6", "6bba")]
    rng = np.random.default_rng(314159)
    draws = {name: [] for name in data}
    for _ in range(50):
        index = np.concatenate([rng.choice(group, size=(200, len(group)), replace=True) for group in groups], axis=1)
        for name, values in data.items():
            draws[name].append(score(values[index]))
    draws = {name: np.concatenate(values) for name, values in draws.items()}
    comparisons = []
    for candidate, baseline in (
        ("candidate_full60_source44_public", "baseline_gapfix90_public"),
        ("candidate_full60_source44_local", "baseline_gapfix90_local"),
        ("candidate_full60_source44_public", "candidate_full60_source44_local"),
    ):
        delta = draws[candidate] - draws[baseline]
        comparisons.append(
            {
                "a": candidate,
                "b": baseline,
                "delta": float(score(data[candidate]) - score(data[baseline])),
                "conditional_movie_95_interval": np.quantile(delta, [0.025, 0.975]).tolist(),
                "leave_one_movie_min_delta": float(
                    min(score(np.delete(data[candidate], i, axis=0)) - score(np.delete(data[baseline], i, axis=0)) for i in range(len(names)))
                ),
                "leave_one_movie_max_delta": float(
                    max(score(np.delete(data[candidate], i, axis=0)) - score(np.delete(data[baseline], i, axis=0)) for i in range(len(names)))
                ),
            }
        )
    result = {
        "status": "PASS_EXP217_FULL60_SOURCE44_COMPARISON",
        "scores": {name: float(score(values)) for name, values in data.items()},
        "by_embryo": {
            name: {prefix: float(score(values[group])) for prefix, group in zip(("44b6", "6bba"), groups)}
            for name, values in data.items()
        },
        "comparisons": comparisons,
        "changed_shards": "Only target6bba source44b6 shards use EXP215 full-cache epoch59 primary.",
        "limitations": [
            "Target44b6 side is reused from EXP214 gapfix90 to isolate the weak source44b6-to-target6bba direction.",
            "Two biological embryos; movie bootstrap is conditional finite-sample uncertainty.",
            "Development-adapted CV; no Kaggle submission authority.",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
