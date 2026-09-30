"""Compare EXP218 short-track rescue against EXP214 gapfix90 public baseline."""
import argparse
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
    expected = {"baseline_gapfix90_public", "candidate_short_track_rescue_public"}
    assert set(metrics["rows"]) == expected
    rows = {name: sorted(values, key=lambda row: row["dataset"]) for name, values in metrics["rows"].items()}
    names = [row["dataset"] for row in rows["baseline_gapfix90_public"]]
    assert len(names) == 175
    assert [row["dataset"] for row in rows["candidate_short_track_rescue_public"]] == names
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
    baseline = "baseline_gapfix90_public"
    candidate = "candidate_short_track_rescue_public"
    delta = draws[candidate] - draws[baseline]
    leave_one = [
        float(score(np.delete(data[candidate], i, axis=0)) - score(np.delete(data[baseline], i, axis=0)))
        for i in range(len(names))
    ]
    per_movie_delta = [
        {
            "dataset": name,
            "delta_edge_jaccard": float(
                rows[candidate][i]["adj_edge_jaccard"] - rows[baseline][i]["adj_edge_jaccard"]
            ),
            "baseline_edge_fn": int(rows[baseline][i]["edge_fn"]),
            "candidate_edge_fn": int(rows[candidate][i]["edge_fn"]),
            "baseline_edge_fp": int(rows[baseline][i]["edge_fp"]),
            "candidate_edge_fp": int(rows[candidate][i]["edge_fp"]),
            "baseline_node_recall": float(rows[baseline][i]["node_recall"]),
            "candidate_node_recall": float(rows[candidate][i]["node_recall"]),
        }
        for i, name in enumerate(names)
    ]
    result = {
        "status": "PASS_EXP218_SHORT_TRACK_RESCUE_COMPARISON",
        "scores": {name: float(score(values)) for name, values in data.items()},
        "by_embryo": {
            name: {prefix: float(score(values[group])) for prefix, group in zip(("44b6", "6bba"), groups)}
            for name, values in data.items()
        },
        "comparison": {
            "a": candidate,
            "b": baseline,
            "delta": float(score(data[candidate]) - score(data[baseline])),
            "conditional_movie_95_interval": np.quantile(delta, [0.025, 0.975]).tolist(),
            "resample_fraction_positive": float(np.mean(delta > 0)),
            "leave_one_movie_min_delta": min(leave_one),
            "leave_one_movie_max_delta": max(leave_one),
        },
        "top_positive_movies": sorted(per_movie_delta, key=lambda row: row["delta_edge_jaccard"], reverse=True)[:15],
        "top_negative_movies": sorted(per_movie_delta, key=lambda row: row["delta_edge_jaccard"])[:15],
        "changed_shards": "Only source44b6 -> target6bba public graph shards enable adaptive short-track rescue.",
        "limitations": [
            "Target44b6 side is reused from EXP214 gapfix90 to isolate target6bba endpoint rescue.",
            "Two biological embryos; movie bootstrap is conditional finite-sample uncertainty.",
            "Development-adapted CV; no Kaggle submission authority.",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
