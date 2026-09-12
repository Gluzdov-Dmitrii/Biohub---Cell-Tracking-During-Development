"""Select synthetic-gap parameters by leave-one-movie-out pooled score."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


DIVISION_WEIGHT = 0.1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarise(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Cannot summarise an empty row set")
    totals = {
        key: sum(int(row[key]) for row in rows)
        for key in ("edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn")
    }
    edge_denom = totals["edge_tp"] + totals["edge_fp"] + totals["edge_fn"]
    division_denom = totals["division_tp"] + totals["division_fp"] + totals["division_fn"]
    edge_jaccard = totals["edge_tp"] / edge_denom if edge_denom else 0.0
    division_jaccard = totals["division_tp"] / division_denom if division_denom else 0.0
    adjusted_rows = [row for row in rows if math.isfinite(float(row["adj_edge_jaccard"]))]
    adjusted_weight = sum(
        int(row["edge_tp"]) + int(row["edge_fp"]) + int(row["edge_fn"])
        for row in adjusted_rows
    )
    adjusted = (
        sum(
            float(row["adj_edge_jaccard"])
            * (int(row["edge_tp"]) + int(row["edge_fp"]) + int(row["edge_fn"]))
            for row in adjusted_rows
        )
        / adjusted_weight
        if adjusted_weight
        else float("nan")
    )
    return {
        **totals,
        "n": len(rows),
        "edge_jaccard": edge_jaccard,
        "division_jaccard": division_jaccard,
        "node_recall": sum(float(row["node_recall"]) for row in rows) / len(rows),
        "adj_edge_jaccard": adjusted,
        "score": adjusted + DIVISION_WEIGHT * division_jaccard,
    }


def parse_variant(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"Variant must be LABEL=PATH, got {spec!r}")
    label, raw_path = spec.split("=", 1)
    if not label or not raw_path:
        raise ValueError(f"Variant must be LABEL=PATH, got {spec!r}")
    return label, Path(raw_path)


def load_direction(specs: list[str]) -> dict[str, dict]:
    variants: dict[str, dict] = {}
    for spec in specs:
        label, path = parse_variant(spec)
        if label in variants:
            raise ValueError(f"Duplicate variant label: {label}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        variants[label] = {"path": str(path), "sha256": sha256(path), "payload": payload}
    if len(variants) < 2:
        raise ValueError("Nested selection requires at least two variants")
    return variants


def select_direction(variants: dict[str, dict], direction: str) -> dict:
    labels = sorted(variants)
    rows_by_label = {
        label: {
            row["dataset"]: row
            for row in variants[label]["payload"]["per_movie_by_arm"]["synthetic_gap_deepcenter"]
        }
        for label in labels
    }
    base_rows = {
        row["dataset"]: row
        for row in variants[labels[0]]["payload"]["per_movie_by_arm"]["registered_hungarian"]
    }
    datasets = sorted(base_rows)
    if len(datasets) < 3:
        raise ValueError(f"{direction}: need at least three movies")
    for label in labels:
        if sorted(rows_by_label[label]) != datasets:
            raise ValueError(f"{direction}/{label}: dataset coverage mismatch")

    selected_rows = []
    selections = []
    for held_out in datasets:
        train_datasets = [name for name in datasets if name != held_out]
        train_scores = {
            label: summarise([rows_by_label[label][name] for name in train_datasets])["score"]
            for label in labels
        }
        selected_label = max(labels, key=lambda label: (train_scores[label], label))
        selected = rows_by_label[selected_label][held_out]
        selected_rows.append(selected)
        selections.append({
            "held_out_dataset": held_out,
            "selected_variant": selected_label,
            "selection_train_score": train_scores[selected_label],
            "held_out_score": float(selected["adj_edge_jaccard"]),
            "held_out_base_score": float(base_rows[held_out]["adj_edge_jaccard"]),
            "held_out_delta": float(selected["adj_edge_jaccard"]) - float(base_rows[held_out]["adj_edge_jaccard"]),
            "all_train_scores": train_scores,
        })

    full_scores = {
        label: summarise([rows_by_label[label][name] for name in datasets])["score"]
        for label in labels
    }
    return {
        "direction": direction,
        "datasets": datasets,
        "base_rows": [base_rows[name] for name in datasets],
        "selected_rows": selected_rows,
        "selections": selections,
        "nested_base_summary": summarise([base_rows[name] for name in datasets]),
        "nested_selected_summary": summarise(selected_rows),
        "full_data_variant_scores_diagnostic_only": full_scores,
        "full_data_oracle_variant_diagnostic_only": max(labels, key=lambda label: (full_scores[label], label)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", action="append", required=True, metavar="LABEL=PATH")
    parser.add_argument("--reverse", action="append", required=True, metavar="LABEL=PATH")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    forward = load_direction(args.forward)
    reverse = load_direction(args.reverse)
    if sorted(forward) != sorted(reverse):
        parser.error("Forward and reverse variant labels must match exactly")
    forward_result = select_direction(forward, "44b6_to_6bba")
    reverse_result = select_direction(reverse, "6bba_to_44b6")
    combined_base = summarise(forward_result["base_rows"] + reverse_result["base_rows"])
    combined_selected = summarise(
        forward_result["selected_rows"] + reverse_result["selected_rows"]
    )
    result = {
        "status": (
            "PASS_NESTED_POOLED_GAIN"
            if combined_selected["score"] > combined_base["score"]
            else "REJECT_NESTED_POOLED_GAIN"
        ),
        "protocol": (
            "Exploratory leave-one-movie-out parameter selection within each reciprocal target "
            "direction. The mechanism family was retained after EXP185, so this is nested "
            "development OOF, not untouched confirmatory OOF."
        ),
        "primary_metric": "combined_nested_pooled_score",
        "variants": {
            label: {
                "forward_path": forward[label]["path"],
                "forward_sha256": forward[label]["sha256"],
                "forward_parameters": forward[label]["payload"]["parameters"],
                "reverse_path": reverse[label]["path"],
                "reverse_sha256": reverse[label]["sha256"],
                "reverse_parameters": reverse[label]["payload"]["parameters"],
            }
            for label in sorted(forward)
        },
        "directions": {"forward": forward_result, "reverse": reverse_result},
        "combined": {
            "base": combined_base,
            "nested_selected": combined_selected,
            "delta": combined_selected["score"] - combined_base["score"],
            "negative_movie_count": sum(
                row["held_out_delta"] < 0
                for result_direction in (forward_result, reverse_result)
                for row in result_direction["selections"]
            ),
        },
        "eligible_for_kaggle_submission": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "combined": result["combined"]}, indent=2))


if __name__ == "__main__":
    main()
