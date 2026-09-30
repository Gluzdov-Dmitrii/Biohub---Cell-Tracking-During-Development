"""Compare development/confirmation input covariates without opening target metrics."""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


PUBLIC_TWINS = {"44b6_0113de3b", "44b6_0b24845f", "6bba_05b6850b", "6bba_05db0fb1"}
MOVIE_PATH = re.compile(r"^train/([^/]+)\.(?:zarr|geff)/")
QUANTILES = ("0.001", "0.01", "0.1", "0.9", "0.99", "0.999")


def stats(values: list[float]) -> dict:
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def standardized_difference(left: list[float], right: list[float]) -> float:
    left_var = statistics.variance(left) if len(left) > 1 else 0.0
    right_var = statistics.variance(right) if len(right) > 1 else 0.0
    pooled_sd = math.sqrt((left_var + right_var) / 2.0)
    return 0.0 if pooled_sd == 0.0 else (statistics.fmean(right) - statistics.fmean(left)) / pooled_sd


def analyze(archive_path: Path, inventory_path: Path, contract_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    development = set(contract["integrity"]["per_movie"]) - PUBLIC_TWINS
    bytes_by_movie: dict[str, int] = defaultdict(int)
    all_movies = set()
    for item in inventory:
        match = MOVIE_PATH.match(str(item["name"]))
        if match:
            movie = match.group(1)
            all_movies.add(movie)
            bytes_by_movie[movie] += int(item.get("bytes", item.get("size", 0)))
    honest = all_movies - PUBLIC_TWINS
    confirmation = honest - development
    if (len(honest), len(development), len(confirmation)) != (195, 20, 175):
        raise ValueError("unexpected honest/development/confirmation cohort sizes")

    metadata = {}
    with zipfile.ZipFile(archive_path) as archive:
        for movie in sorted(honest):
            root = json.loads(archive.read(f"train/{movie}.zarr/zarr.json"))
            array = json.loads(archive.read(f"train/{movie}.zarr/0/zarr.json"))
            quantiles = root["attributes"]["image_statistics"]["quantiles"]
            shape = [int(value) for value in array["shape"]]
            metadata[movie] = {
                "shape": shape,
                "log_bytes": math.log(float(bytes_by_movie[movie])),
                **{f"q_{key}": float(quantiles[key]) for key in QUANTILES},
            }

    groups = {}
    comparisons = {}
    for prefix in ("44b6", "6bba"):
        dev_names = sorted(name for name in development if name.startswith(prefix + "_"))
        conf_names = sorted(name for name in confirmation if name.startswith(prefix + "_"))
        groups[prefix] = {}
        for label, names in (("development", dev_names), ("confirmation", conf_names)):
            groups[prefix][label] = {
                "movies": len(names),
                "shape_counts": dict(sorted(Counter("x".join(map(str, metadata[name]["shape"])) for name in names).items())),
                "log_bytes": stats([metadata[name]["log_bytes"] for name in names]),
                "image_quantiles": {key: stats([metadata[name][f"q_{key}"] for name in names]) for key in QUANTILES},
            }
        comparisons[prefix] = {
            "standardized_confirmation_minus_development": {
                "log_bytes": standardized_difference(
                    [metadata[name]["log_bytes"] for name in dev_names],
                    [metadata[name]["log_bytes"] for name in conf_names],
                ),
                **{
                    f"q_{key}": standardized_difference(
                        [metadata[name][f"q_{key}"] for name in dev_names],
                        [metadata[name][f"q_{key}"] for name in conf_names],
                    )
                    for key in QUANTILES
                },
            }
        }
    return {
        "status": "PASS_EXP192_INPUT_COVARIATE_AUDIT",
        "scope": "Input-only aggregate diagnostics; no graph, label, score, or per-movie metric was read.",
        "anti_adaptation": "These summaries cannot alter EXP192's frozen models, parameters, cohort, or promotion gates.",
        "cohorts": {"honest": 195, "development": 20, "confirmation": 175},
        "groups": groups,
        "comparisons": comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--official24-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.archive, args.inventory, args.official24_contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
