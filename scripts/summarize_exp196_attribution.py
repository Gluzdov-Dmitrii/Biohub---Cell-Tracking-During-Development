"""Combine directional EXP196 error decompositions with stratified uncertainty."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


ENDPOINT_KEYS = (
    "fn_missing_both_endpoints",
    "fn_missing_source_endpoint",
    "fn_missing_target_endpoint",
)
ASSOCIATION_KEY = "fn_both_endpoints_matched_link_missing"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def endpoint_and_association(rows: list[dict]) -> tuple[int, int]:
    endpoint = sum(sum(int(row[key]) for key in ENDPOINT_KEYS) for row in rows)
    association = sum(int(row[ASSOCIATION_KEY]) for row in rows)
    return endpoint, association


def fraction(rows: list[dict]) -> float:
    endpoint, association = endpoint_and_association(rows)
    denominator = endpoint + association
    if denominator == 0:
        raise ValueError("no false-negative edge mass")
    return endpoint / denominator


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def combine(
    forward: dict,
    reverse: dict,
    *,
    draws: int = 20_000,
    seed: int = 314159,
) -> dict:
    for label, payload, prefix in (
        ("forward", forward, "6bba_"),
        ("reverse", reverse, "44b6_"),
    ):
        if payload.get("status") != "PASS_OFFICIAL_MATCH_EDGE_FAILURE_DECOMPOSITION":
            raise ValueError(f"{label}: invalid status")
        rows = payload.get("per_movie", [])
        names = [str(row["dataset"]) for row in rows]
        if len(names) != 12 or len(set(names)) != 12:
            raise ValueError(f"{label}: expected 12 unique movies")
        if any(not name.startswith(prefix) for name in names):
            raise ValueError(f"{label}: wrong embryo prefix")
    forward_rows = forward["per_movie"]
    reverse_rows = reverse["per_movie"]
    if set(row["dataset"] for row in forward_rows) & set(row["dataset"] for row in reverse_rows):
        raise ValueError("direction movie sets overlap")

    rng = random.Random(seed)
    bootstrap: list[float] = []
    for _ in range(draws):
        sample = [rng.choice(forward_rows) for _ in forward_rows]
        sample.extend(rng.choice(reverse_rows) for _ in reverse_rows)
        bootstrap.append(fraction(sample))
    all_rows = forward_rows + reverse_rows
    endpoint, association = endpoint_and_association(all_rows)
    return {
        "status": "PASS_EXP196_DIRECTIONAL_ATTRIBUTION_SUMMARY",
        "movies": 24,
        "directional": {
            "forward": {
                "endpoint_limited_fn_fraction": fraction(forward_rows),
                "endpoint_limited_fn": endpoint_and_association(forward_rows)[0],
                "association_limited_fn": endpoint_and_association(forward_rows)[1],
            },
            "reverse": {
                "endpoint_limited_fn_fraction": fraction(reverse_rows),
                "endpoint_limited_fn": endpoint_and_association(reverse_rows)[0],
                "association_limited_fn": endpoint_and_association(reverse_rows)[1],
            },
        },
        "pooled": {
            "endpoint_limited_fn": endpoint,
            "association_limited_fn": association,
            "endpoint_limited_fn_fraction": endpoint / (endpoint + association),
            "association_limited_fn_fraction": association / (endpoint + association),
        },
        "movie_stratified_bootstrap": {
            "draws": draws,
            "seed": seed,
            "endpoint_fraction_ci95": [quantile(bootstrap, 0.025), quantile(bootstrap, 0.975)],
            "probability_endpoint_fraction_gt_half": sum(x > 0.5 for x in bootstrap) / draws,
        },
        "evidence_class": "Exploratory 24-movie development attribution; mechanism routing only.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=314159)
    args = parser.parse_args()
    forward = json.loads(args.forward.read_text(encoding="utf-8"))
    reverse = json.loads(args.reverse.read_text(encoding="utf-8"))
    result = combine(forward, reverse, draws=args.draws, seed=args.seed)
    result["inputs"] = {
        "forward": {"path": str(args.forward), "sha256": sha256(args.forward)},
        "reverse": {"path": str(args.reverse), "sha256": sha256(args.reverse)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
