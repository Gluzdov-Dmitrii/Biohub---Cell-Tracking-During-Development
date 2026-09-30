"""Freeze one centroid arm from source-only validation, including translation fallback."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from evaluate_cached_intensity_centroid_refinement import sha256


def select(result_path: Path, arm_order: list[str]) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "PASS_FIXED_INTENSITY_CENTROID_FAMILY":
        raise RuntimeError("source family did not pass")
    if not arm_order or arm_order[0] != "translation" or len(set(arm_order)) != len(arm_order):
        raise RuntimeError("arm order must be unique and start with translation")
    summaries = result["summary_by_arm"]
    if set(summaries) != set(arm_order):
        raise RuntimeError("arm order does not exactly cover source arms")
    datasets = None
    rows_by_arm = result["per_movie_by_arm"]
    for arm in arm_order:
        current = [row["dataset"] for row in rows_by_arm[arm]]
        if len(current) != len(set(current)) or not current:
            raise RuntimeError("invalid per-movie coverage")
        if datasets is None:
            datasets = current
        elif current != datasets:
            raise RuntimeError("arm movie order differs")
    scores = {arm: float(summaries[arm]["score"]) for arm in arm_order}
    if not all(math.isfinite(value) for value in scores.values()):
        raise RuntimeError("nonfinite source score")
    best = max(scores.values())
    selected = next(arm for arm in arm_order if abs(scores[arm] - best) <= 1e-12)
    radius = None
    if selected != "translation":
        prefix = "intensity_centroid_r"
        if not selected.startswith(prefix):
            raise RuntimeError("unexpected centroid arm name")
        radius = [int(item) for item in selected[len(prefix):].split("_")]
        if len(radius) != 3:
            raise RuntimeError("invalid selected radius")
    return {
        "status": "PASS_SOURCE_ONLY_CENTROID_SELECTION",
        "source_result": str(result_path),
        "source_result_sha256": sha256(result_path),
        "movies": len(datasets or []),
        "arm_preference_order": arm_order,
        "scores": scores,
        "selected_arm": selected,
        "selected_radius_zyx_voxels": radius,
        "selected_delta_vs_translation": scores[selected] - scores["translation"],
        "selection_scope": "Source checkpoint-validation movies only; target metrics must remain unopened until this receipt is frozen.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-result", type=Path, required=True)
    parser.add_argument("--arm-order", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = select(args.source_result, args.arm_order)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
