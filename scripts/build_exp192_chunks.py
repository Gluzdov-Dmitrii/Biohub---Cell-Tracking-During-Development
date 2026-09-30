"""Freeze lexicographic EXP192 chunks without opening any competition data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def chunked(values: list[str], maximum: int) -> list[list[str]]:
    if maximum <= 0:
        raise ValueError("maximum must be positive")
    if len(values) != len(set(values)):
        raise ValueError("duplicate movie")
    ordered = sorted(values)
    return [ordered[index:index + maximum] for index in range(0, len(ordered), maximum)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--maximum", type=int, default=24)
    args = parser.parse_args()
    inputs = {
        "forward": json.loads(args.forward.read_text(encoding="utf-8"))["target_development"],
        "reverse": json.loads(args.reverse.read_text(encoding="utf-8"))["target_development"],
    }
    expected = {"forward": 116, "reverse": 59}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    index = {"maximum_movies_per_chunk": args.maximum, "chunks": []}
    for direction, movies in inputs.items():
        if len(movies) != expected[direction]:
            raise ValueError(f"{direction}: expected {expected[direction]} movies")
        for number, members in enumerate(chunked(movies, args.maximum)):
            path = args.output_dir / f"{direction}_{number:02d}.json"
            path.write_text(json.dumps({"target_development": members}, indent=2) + "\n", encoding="utf-8")
            index["chunks"].append({
                "direction": direction,
                "number": number,
                "movies": len(members),
                "first": members[0],
                "last": members[-1],
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    index_path = args.output_dir / "chunk_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
