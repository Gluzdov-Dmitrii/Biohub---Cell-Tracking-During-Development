"""Gate all eight EXP211 D4 chunks before any 175-movie metric is opened."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from validate_exp211_d4_chunk_structure import sha256


MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def verify_manifest(path: Path) -> tuple[int, str]:
    entries = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = MANIFEST_LINE.fullmatch(raw)
        if not match:
            raise ValueError(f"Malformed manifest line {number}: {path}")
        target = Path(match.group(2))
        if not target.is_absolute() or not target.is_file():
            raise ValueError(f"Missing or non-absolute manifest target: {target}")
        if sha256(target) != match.group(1):
            raise ValueError(f"Manifest hash mismatch: {target}")
        entries += 1
    if entries < 10:
        raise ValueError(f"Manifest unexpectedly small: {path}")
    return entries, sha256(path)


def validate_all(chunk_index_path: Path, runs_root: Path) -> dict:
    index = json.loads(chunk_index_path.read_text(encoding="utf-8"))
    chunks = index.get("chunks")
    expected_keys = {
        *(("forward", number) for number in range(5)),
        *(("reverse", number) for number in range(3)),
    }
    if not isinstance(chunks, list) or len(chunks) != 8:
        raise ValueError("Expected exactly eight chunks")
    if {(str(row["direction"]), int(row["number"])) for row in chunks} != expected_keys:
        raise ValueError("Frozen chunk keys mismatch")

    seen = {"forward": [], "reverse": []}
    validations = []
    for row in sorted(chunks, key=lambda item: (str(item["direction"]), int(item["number"]))):
        direction = str(row["direction"])
        number = int(row["number"])
        run = runs_root / f"exp211_{direction}_{number:02d}_20260912"
        movies_path = run / "movies.json"
        if sha256(movies_path) != row["sha256"]:
            raise ValueError(f"{direction}_{number:02d}: movie SHA mismatch")
        movies = json.loads(movies_path.read_text(encoding="utf-8"))["target_development"]
        if len(movies) != int(row["movies"]) or len(movies) != len(set(movies)):
            raise ValueError(f"{direction}_{number:02d}: movie count/uniqueness mismatch")
        structure_path = run / "results" / "structure_validation.json"
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
        if structure.get("status") != "PASS_EXP211_D4_CHUNK_STRUCTURE_NO_METRICS":
            raise ValueError(f"{direction}_{number:02d}: structure gate failed")
        if structure.get("direction") != direction or structure.get("movie_count") != len(movies):
            raise ValueError(f"{direction}_{number:02d}: structure identity mismatch")
        if structure.get("movies_sha256") != row["sha256"]:
            raise ValueError(f"{direction}_{number:02d}: structure movie SHA mismatch")
        if structure.get("scientific_metrics_emitted") is not False:
            raise ValueError(f"{direction}_{number:02d}: metric-emission flag mismatch")
        entries, manifest_sha = verify_manifest(run / "SHA256SUMS")
        seen[direction].extend(movies)
        validations.append({
            "chunk": f"{direction}_{number:02d}",
            "movies": len(movies),
            "movies_sha256": row["sha256"],
            "manifest_entries": entries,
            "manifest_sha256": manifest_sha,
            "structure_sha256": sha256(structure_path),
        })

    expected_counts = {"forward": 116, "reverse": 59}
    for direction, movies in seen.items():
        if len(movies) != expected_counts[direction] or len(set(movies)) != expected_counts[direction]:
            raise ValueError(f"{direction}: exact union mismatch")
        prefix = "6bba_" if direction == "forward" else "44b6_"
        if any(not movie.startswith(prefix) for movie in movies):
            raise ValueError(f"{direction}: prefix mismatch")
    if set(seen["forward"]) & set(seen["reverse"]):
        raise ValueError("Direction overlap")

    return {
        "status": "PASS_EXP211_ALL_D4_CHUNKS_NO_METRICS",
        "chunks": 8,
        "movie_count": 175,
        "direction_counts": expected_counts,
        "validations": validations,
        "scientific_metrics_emitted": False,
        "next_allowed_step": "Merge D4 rows and build only the preregistered policies.",
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
    print(json.dumps({key: result[key] for key in ("status", "chunks", "movie_count", "scientific_metrics_emitted")}, sort_keys=True))


if __name__ == "__main__":
    main()

