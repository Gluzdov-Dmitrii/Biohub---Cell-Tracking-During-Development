"""Validate compute-matched D4 feature-TTA controls before scoring comparisons."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from select_nested_pooled_synthetic_gap import sha256
from validate_cached_arm_metrics_reproduction import NUMERIC_FIELDS, arm_rows


def metric_error(left: dict, right: dict, left_arm: str, right_arm: str) -> float:
    expected = arm_rows(left, left_arm)
    actual = arm_rows(right, right_arm)
    if sorted(expected) != sorted(actual):
        raise ValueError("metric movie coverage mismatch")
    return max(
        abs(float(expected[movie][field]) - float(actual[movie][field]))
        for movie in expected
        for field in NUMERIC_FIELDS
    )


def compare_cache_dirs(off_dir: Path, on_dir: Path, movies: list[str]) -> dict:
    changed_edge_movies = []
    manifests = []
    for name in movies:
        stem = Path(name).stem
        off_path = off_dir / f"{stem}.npz"
        on_path = on_dir / f"{stem}.npz"
        with np.load(off_path) as off, np.load(on_path) as on:
            if not np.array_equal(off["coords"], on["coords"]):
                raise ValueError(f"{name}: coordinate drift between feature arms")
            edge_equal = all(
                np.array_equal(off[key], on[key])
                for key in ("edge_source", "edge_target", "edge_probability", "edge_distance")
            )
        if not edge_equal:
            changed_edge_movies.append(name)
        manifests.append(
            {
                "dataset": name,
                "feature_off_sha256": sha256(off_path),
                "feature_on_sha256": sha256(on_path),
            }
        )
    return {"changed_edge_movies": changed_edge_movies, "cache_manifest": manifests}


def main() -> None:
    parser = argparse.ArgumentParser()
    for direction in ("forward", "reverse"):
        parser.add_argument(f"--{direction}-movies", type=Path, required=True)
        parser.add_argument(f"--{direction}-off-raw", type=Path, required=True)
        parser.add_argument(f"--{direction}-on-raw", type=Path, required=True)
        parser.add_argument(f"--{direction}-off-filtered", type=Path, required=True)
        parser.add_argument(f"--{direction}-on-filtered", type=Path, required=True)
        parser.add_argument(f"--{direction}-off-cache", type=Path, required=True)
        parser.add_argument(f"--{direction}-on-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = {"status": "PASS_EXP207_D4_FEATURE_CONTROLS", "directions": {}}
    changed_total = 0
    for direction, minimum in (("forward", 8), ("reverse", 3)):
        movies_path = getattr(args, f"{direction}_movies")
        movies = json.loads(movies_path.read_text(encoding="utf-8"))["target_development"]
        off_raw_path = getattr(args, f"{direction}_off_raw")
        on_raw_path = getattr(args, f"{direction}_on_raw")
        off_filtered_path = getattr(args, f"{direction}_off_filtered")
        on_filtered_path = getattr(args, f"{direction}_on_filtered")
        off_raw = json.loads(off_raw_path.read_text(encoding="utf-8"))
        on_raw = json.loads(on_raw_path.read_text(encoding="utf-8"))
        off_filtered = json.loads(off_filtered_path.read_text(encoding="utf-8"))
        on_filtered = json.loads(on_filtered_path.read_text(encoding="utf-8"))
        raw_error = metric_error(
            off_raw, on_raw, "registered_hungarian", "registered_hungarian"
        )
        filtered_error = metric_error(off_filtered, on_filtered, f"min{minimum}", f"min{minimum}")
        if raw_error > 1e-12 or filtered_error > 1e-12:
            raise ValueError(
                f"{direction}: coordinate-linker metric drift raw={raw_error} filtered={filtered_error}"
            )
        cache = compare_cache_dirs(
            getattr(args, f"{direction}_off_cache"),
            getattr(args, f"{direction}_on_cache"),
            movies,
        )
        changed_total += len(cache["changed_edge_movies"])
        result["directions"][direction] = {
            "movies": len(movies),
            "raw_registered_maximum_absolute_error": raw_error,
            "filtered_registered_maximum_absolute_error": filtered_error,
            **cache,
        }
    if changed_total == 0:
        raise ValueError("feature TTA did not change any cached learned edge values")
    result["changed_edge_movies"] = changed_total
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
