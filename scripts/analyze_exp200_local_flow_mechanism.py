"""Attribute fixed local-flow gains without selecting another policy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from select_nested_pooled_synthetic_gap import summarise


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correlation(x: list[float], y: list[float]) -> dict:
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("correlation requires matching vectors with at least three values")
    if np.std(x) <= 1e-15 or np.std(y) <= 1e-15:
        return {"pearson": None, "spearman": None}
    return {
        "pearson": float(np.corrcoef(x, y)[0, 1]),
        "spearman": float(spearmanr(x, y).statistic),
    }


def analyze_direction(
    flow: dict,
    attribution: dict,
    arm: str,
    expected_prefix: str,
    expected_count: int = 12,
) -> dict:
    base = {row["dataset"]: row for row in flow["per_movie_by_arm"]["translation"]}
    candidate = {row["dataset"]: row for row in flow["per_movie_by_arm"][arm]}
    errors = {row["dataset"]: row for row in attribution["per_movie"]}
    telemetry = {row["dataset"]: row["variants"][arm] for row in flow["telemetry"]}
    names = sorted(base)
    if not (
        len(names) == expected_count
        and set(candidate) == set(errors) == set(telemetry) == set(names)
        and all(name.startswith(expected_prefix + "_") for name in names)
    ):
        raise ValueError("direction coverage mismatch")
    rows = []
    for name in names:
        b, c, e, t = base[name], candidate[name], errors[name], telemetry[name]
        endpoint_fn = int(e["fn_missing_both_endpoints"]) + int(e["fn_missing_source_endpoint"]) + int(e["fn_missing_target_endpoint"])
        association_fn = int(e["fn_both_endpoints_matched_link_missing"])
        if endpoint_fn + association_fn != int(b["edge_fn"]):
            raise ValueError(f"{name}: EXP196 FN partition mismatch")
        frames = list(t["frames"])
        correction = [float(frame["median_correction_um"]) for frame in frames]
        pairs = [float(frame["mutual_pairs"]) for frame in frames]
        rows.append({
            "dataset": name,
            "delta_score": float(c["adj_edge_jaccard"]) - float(b["adj_edge_jaccard"]),
            "delta_edge_tp": int(c["edge_tp"]) - int(b["edge_tp"]),
            "delta_edge_fp": int(c["edge_fp"]) - int(b["edge_fp"]),
            "delta_edge_fn": int(c["edge_fn"]) - int(b["edge_fn"]),
            "delta_node_recall": float(c["node_recall"]) - float(b["node_recall"]),
            "association_fn_share": association_fn / max(1, endpoint_fn + association_fn),
            "mean_frame_median_correction_um": float(np.mean(correction)),
            "mean_mutual_pairs": float(np.mean(pairs)),
        })
    deltas = [row["delta_score"] for row in rows]
    return {
        "arm": arm,
        "base_summary": summarise([base[name] for name in names]),
        "candidate_summary": summarise([candidate[name] for name in names]),
        "sufficient_stat_delta": {
            key: sum(int(candidate[name][key]) - int(base[name][key]) for name in names)
            for key in ("edge_tp", "edge_fp", "edge_fn")
        },
        "movie_counts": {
            "positive": sum(value > 0 for value in deltas),
            "negative": sum(value < 0 for value in deltas),
            "tie": sum(value == 0 for value in deltas),
        },
        "correlation_with_delta_score": {
            "association_fn_share": correlation(
                [row["association_fn_share"] for row in rows], deltas
            ),
            "mean_frame_median_correction_um": correlation(
                [row["mean_frame_median_correction_um"] for row in rows], deltas
            ),
            "mean_mutual_pairs": correlation(
                [row["mean_mutual_pairs"] for row in rows], deltas
            ),
        },
        "per_movie": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-flow", type=Path, required=True)
    parser.add_argument("--reverse-flow", type=Path, required=True)
    parser.add_argument("--forward-attribution", type=Path, required=True)
    parser.add_argument("--reverse-attribution", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.forward_flow, args.reverse_flow, args.forward_attribution, args.reverse_attribution]
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    directions = {
        "forward": analyze_direction(payloads[0], payloads[2], "flow_k32_a050", "6bba"),
        "reverse": analyze_direction(payloads[1], payloads[3], "flow_k16_a025", "44b6"),
    }
    base = directions["forward"]["base_summary"]
    reverse_base = directions["reverse"]["base_summary"]
    candidate = directions["forward"]["candidate_summary"]
    reverse_candidate = directions["reverse"]["candidate_summary"]
    result = {
        "status": "PASS_EXP200_LOCAL_FLOW_MECHANISM_ATTRIBUTION",
        "scope": "Post-hoc diagnostic only; no threshold, arm or gate selection.",
        "directions": directions,
        "pooled_sufficient_stat_delta": {
            key: directions["forward"]["sufficient_stat_delta"][key]
            + directions["reverse"]["sufficient_stat_delta"][key]
            for key in ("edge_tp", "edge_fp", "edge_fn")
        },
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in paths],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "pooled_sufficient_stat_delta": result["pooled_sufficient_stat_delta"],
        "direction_diagnostics": {
            name: {
                "movie_counts": value["movie_counts"],
                "correlations": value["correlation_with_delta_score"],
            }
            for name, value in directions.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
