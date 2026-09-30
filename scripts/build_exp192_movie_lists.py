"""Derive immutable per-direction movie lists from the frozen EXP192 manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PUBLIC_TWINS = {
    "44b6_0113de3b",
    "44b6_0b24845f",
    "6bba_05b6850b",
    "6bba_05db0fb1",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(payload: dict) -> dict[str, list[str]]:
    movies = list(payload["missing"]["movies"])
    if len(movies) != 175 or len(set(movies)) != 175:
        raise ValueError("EXP192 requires exactly 175 unique missing movies")
    if set(movies) & PUBLIC_TWINS:
        raise ValueError("public twin leaked into EXP192 confirmation cohort")
    result = {
        "44b6_target": sorted(f"{name}.zarr" for name in movies if name.startswith("44b6_")),
        "6bba_target": sorted(f"{name}.zarr" for name in movies if name.startswith("6bba_")),
    }
    if len(result["44b6_target"]) != 59 or len(result["6bba_target"]) != 116:
        raise ValueError("unexpected EXP192 prefix counts")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    lists = derive(payload)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = {}
    for key, movies in lists.items():
        path = args.output_dir / f"{key}.json"
        path.write_text(json.dumps({"target_development": movies}, indent=2) + "\n", encoding="utf-8")
        output[key] = {"path": str(path), "movies": len(movies), "sha256": digest(path)}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
