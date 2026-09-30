"""Gate EXP192 aggregation after eight structurally valid chunks, without scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_exp192_chunk_structure import sha256, validate as validate_chunk


EXPECTED_LABELS = {
    "forward_00", "forward_01", "forward_02", "forward_03", "forward_04",
    "reverse_00", "reverse_01", "reverse_02",
}


def validate_all(chunk_index_path: Path, runs_root: Path) -> dict:
    index = json.loads(chunk_index_path.read_text(encoding="utf-8"))
    chunks = list(index["chunks"])
    labels = {f"{row['direction']}_{int(row['number']):02d}" for row in chunks}
    if labels != EXPECTED_LABELS or len(chunks) != 8:
        raise ValueError("unexpected frozen chunk index")
    by_direction = {"forward": [], "reverse": []}
    validations = []
    for row in sorted(chunks, key=lambda item: (str(item["direction"]), int(item["number"]))):
        direction = str(row["direction"])
        label = f"{direction}_{int(row['number']):02d}"
        run_id = f"exp192_confirm_{label}_20260911"
        run_dir = runs_root / run_id
        movies_path = run_dir / "movies.json"
        actual_sha = sha256(movies_path)
        if actual_sha != row["sha256"]:
            raise ValueError(f"{label}: movie-list hash mismatch")
        movies = list(json.loads(movies_path.read_text(encoding="utf-8"))["target_development"])
        if len(movies) != int(row["movies"]):
            raise ValueError(f"{label}: movie count mismatch")
        by_direction[direction].extend(movies)
        structural = validate_chunk(run_dir, direction)
        if structural["movie_count"] != len(movies) or structural["scientific_metrics_emitted"] is not False:
            raise ValueError(f"{label}: invalid no-metric structural receipt")
        validations.append({
            "run_id": run_id,
            "direction": direction,
            "movie_count": len(movies),
            "movies_sha256": actual_sha,
            "validated_file_sha256": [item["sha256"] for item in structural["validated_files"]],
        })
    expected = {"forward": (116, "6bba_"), "reverse": (59, "44b6_")}
    union = []
    for direction, (count, prefix) in expected.items():
        names = by_direction[direction]
        if len(names) != count or len(set(names)) != count or any(not name.startswith(prefix) for name in names):
            raise ValueError(f"{direction}: frozen coverage mismatch")
        union.extend(names)
    if len(union) != 175 or len(set(union)) != 175:
        raise ValueError("combined 175-movie coverage mismatch")
    return {
        "status": "PASS_EXP192_ALL_CHUNKS_NO_METRICS",
        "chunk_index_sha256": sha256(chunk_index_path),
        "chunks": 8,
        "movie_counts": {"forward": 116, "reverse": 59, "combined": 175},
        "validations": validations,
        "scientific_metrics_emitted": False,
        "next_allowed_step": "Merge immutable chunk result JSON files, then compute frozen 175-movie policies and stability before inspecting metrics.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-index", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_all(args.chunk_index, args.runs_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "chunks", "movie_counts", "scientific_metrics_emitted")}, indent=2))


if __name__ == "__main__":
    main()
