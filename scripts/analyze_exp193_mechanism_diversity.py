"""Quantify movie-level error diversity among frozen Biohub mechanisms."""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


TOLERANCE = 1e-12


def paired_rows(paths: list[Path], base_arm: str, candidate_arm: str) -> tuple[list[dict], list[dict]]:
    base, selected = [], []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        base.extend(payload["per_movie_by_arm"][base_arm])
        selected.extend(payload["per_movie_by_arm"][candidate_arm])
    return sorted(base, key=lambda row: row["dataset"]), sorted(selected, key=lambda row: row["dataset"])


def nested_rows(path: Path) -> tuple[list[dict], list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    base, selected = [], []
    for direction in ("forward", "reverse"):
        base.extend(payload["directions"][direction]["base_rows"])
        selected.extend(payload["directions"][direction]["selected_rows"])
    return sorted(base, key=lambda row: row["dataset"]), sorted(selected, key=lambda row: row["dataset"])


def rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average = (start + end - 1) / 2.0
        for position in range(start, end):
            result[order[position]] = average
        start = end
    return result


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or not left:
        raise ValueError("correlation vectors must be equally non-empty")
    lm = sum(left) / len(left)
    rm = sum(right) / len(right)
    numerator = sum((x - lm) * (y - rm) for x, y in zip(left, right))
    denominator = math.sqrt(sum((x - lm) ** 2 for x in left) * sum((y - rm) ** 2 for y in right))
    return None if denominator == 0.0 else numerator / denominator


def baseline_max_error(reference: list[dict], candidate: list[dict]) -> float:
    if [row["dataset"] for row in reference] != [row["dataset"] for row in candidate]:
        raise ValueError("baseline movie coverage mismatch")
    maximum = 0.0
    for left, right in zip(reference, candidate):
        if set(left) != set(right):
            raise ValueError("baseline row schemas differ")
        for key in left:
            if key == "dataset":
                continue
            maximum = max(maximum, abs(float(left[key]) - float(right[key])))
    return maximum


def analyze(mechanisms: dict[str, tuple[list[dict], list[dict]]]) -> dict:
    reference_name = "nested_short_component_pruning"
    reference_base = mechanisms[reference_name][0]
    names = [row["dataset"] for row in reference_base]
    if len(names) != 24 or len(set(names)) != 24:
        raise ValueError("expected 24 unique development movies")
    controls = {}
    deltas = {}
    summaries = {}
    for name, (base, selected) in mechanisms.items():
        error = baseline_max_error(reference_base, base)
        if error > TOLERANCE:
            raise ValueError(f"{name}: baseline differs by {error}")
        if [row["dataset"] for row in base] != [row["dataset"] for row in selected]:
            raise ValueError(f"{name}: selected coverage mismatch")
        vector = [float(s["adj_edge_jaccard"]) - float(b["adj_edge_jaccard"]) for b, s in zip(base, selected)]
        deltas[name] = dict(zip(names, vector))
        base_summary, selected_summary = summarise(base), summarise(selected)
        controls[name] = error
        summaries[name] = {
            "pooled_score_delta": selected_summary["score"] - base_summary["score"],
            "pooled_edge_jaccard_delta": selected_summary["edge_jaccard"] - base_summary["edge_jaccard"],
            "node_recall_delta": selected_summary["node_recall"] - base_summary["node_recall"],
            "positive_movies": sum(value > TOLERANCE for value in vector),
            "negative_movies": sum(value < -TOLERANCE for value in vector),
            "zero_movies": sum(abs(value) <= TOLERANCE for value in vector),
        }
    pairs = {}
    for left, right in itertools.combinations(sorted(mechanisms), 2):
        pair = {}
        for scope, selected_names in (
            ("pooled24", names),
            ("target_44b6", [name for name in names if name.startswith("44b6_")]),
            ("target_6bba", [name for name in names if name.startswith("6bba_")]),
        ):
            lv = [deltas[left][name] for name in selected_names]
            rv = [deltas[right][name] for name in selected_names]
            pair[scope] = {
                "pearson": pearson(lv, rv),
                "spearman": pearson(rank(lv), rank(rv)),
                "sign_disagreement": sum(
                    (x > TOLERANCE and y < -TOLERANCE) or (x < -TOLERANCE and y > TOLERANCE)
                    for x, y in zip(lv, rv)
                ),
                "left_positive_right_nonpositive": sum(x > TOLERANCE and y <= TOLERANCE for x, y in zip(lv, rv)),
                "right_positive_left_nonpositive": sum(y > TOLERANCE and x <= TOLERANCE for x, y in zip(lv, rv)),
            }
        pairs[f"{left}__vs__{right}"] = pair
    return {
        "status": "PASS_EXP193_MECHANISM_DIVERSITY",
        "evidence_class": "Exploratory 24-movie development OOF; correlations nominate graph-level tests but are not ensemble scores.",
        "baseline_maximum_absolute_errors": controls,
        "mechanisms": summaries,
        "pairwise_delta_diagnostics": pairs,
        "score_vector_ensemble_forbidden": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp154-forward", type=Path, required=True)
    parser.add_argument("--exp154-reverse", type=Path, required=True)
    parser.add_argument("--exp185-forward", type=Path, required=True)
    parser.add_argument("--exp185-reverse", type=Path, required=True)
    parser.add_argument("--exp186-nested", type=Path, required=True)
    parser.add_argument("--exp190-nested", type=Path, required=True)
    parser.add_argument("--exp191-nested", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    mechanisms = {
        "external_fixed_coordinate_edges": paired_rows([args.exp154_forward, args.exp154_reverse], "registered_hungarian", "registered_plus_native_guided_division"),
        "fixed_synthetic_gap": paired_rows([args.exp185_forward, args.exp185_reverse], "registered_hungarian", "synthetic_gap_deepcenter"),
        "nested_synthetic_gap": nested_rows(args.exp186_nested),
        "nested_short_component_pruning": nested_rows(args.exp190_nested),
        "nested_gap_plus_pruning": nested_rows(args.exp191_nested),
    }
    result = analyze(mechanisms)
    result["inputs"] = {
        key: {"path": str(value), "sha256": sha256(value)}
        for key, value in vars(args).items() if key != "output"
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
