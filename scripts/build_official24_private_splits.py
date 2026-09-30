"""Audit the official 24-movie download and freeze private-first reciprocal splits.

The split has three distinct roles per reciprocal embryo fold:

* 10 source-embryo movies train the model;
* 2 source-embryo movies select the checkpoint without seeing target biology;
* 4 target-embryo movies are a development stress test and the final 8 target
  movies stay locked until a complete candidate is frozen.

The locked audit is not a population confidence interval: only two embryo
domains are available.  It is nevertheless materially safer than random
movie CV because no target-embryo movie participates in fitting or checkpoint
selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


EMBRYOS = ("44b6", "6bba")
MOVIES_PER_EMBRYO = 12
ZARR_FILES_PER_MOVIE = 102
GEFF_FILES_PER_MOVIE = 21


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_manifest_path(name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or relative.parts[0] != "train":
        raise ValueError(f"unsafe or out-of-scope manifest path: {name!r}")
    if any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError(f"unsafe manifest path component: {name!r}")
    return Path(*relative.parts)


def content_tree_sha256(root: Path, entries: list[dict[str, object]]) -> str:
    """Hash names, sizes and bytes so later copies can prove content identity."""
    digest = hashlib.sha256()
    for item in sorted(entries, key=lambda row: str(row["name"])):
        name = str(item["name"])
        path = root / safe_manifest_path(name)
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(int(item["size"])).encode("ascii") + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--contract-output", type=Path, required=True)
    parser.add_argument("--trainer-output", type=Path, required=True)
    parser.add_argument(
        "--content-hash",
        action="store_true",
        help="Compute reproducibility hashes over every verified training byte.",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = [item for item in manifest["files"] if str(item["name"]).startswith("train/")]
    relevant = []
    for item in entries:
        name = str(item["name"])
        relative = safe_manifest_path(name)
        if len(relative.parts) >= 2 and relative.parts[1].startswith(EMBRYOS):
            relevant.append({"name": name, "size": int(item["size"])})
    if len(relevant) != 2 * MOVIES_PER_EMBRYO * (ZARR_FILES_PER_MOVIE + GEFF_FILES_PER_MOVIE):
        raise RuntimeError(f"unexpected official manifest entry count: {len(relevant)}")

    names = [str(item["name"]) for item in relevant]
    if len(names) != len(set(names)):
        raise RuntimeError("duplicate paths in official manifest")
    for name in names:
        safe_manifest_path(name)

    problems: list[dict[str, object]] = []
    by_movie: dict[str, dict[str, int]] = {}
    entries_by_movie: dict[str, list[dict[str, object]]] = {}
    metadata_json_files = 0
    for item in relevant:
        relative = safe_manifest_path(str(item["name"]))
        movie = relative.parts[1].rsplit(".", 1)[0]
        entries_by_movie.setdefault(movie, []).append(item)
        kind = "zarr" if relative.parts[1].endswith(".zarr") else "geff"
        row = by_movie.setdefault(movie, {"zarr_files": 0, "geff_files": 0, "bytes": 0})
        row[f"{kind}_files"] += 1
        row["bytes"] += item["size"]
        actual = args.data_root / relative
        if not actual.is_file():
            problems.append({"name": item["name"], "problem": "missing"})
        elif actual.stat().st_size != item["size"]:
            problems.append(
                {
                    "name": item["name"],
                    "problem": "size_mismatch",
                    "expected": item["size"],
                    "actual": actual.stat().st_size,
                }
            )
        elif actual.name == "zarr.json":
            metadata_json_files += 1
            try:
                metadata = json.loads(actual.read_text(encoding="utf-8"))
                if metadata.get("zarr_format") != 3 or metadata.get("node_type") not in ("array", "group"):
                    raise ValueError("unexpected Zarr v3 metadata")
            except Exception as error:
                problems.append({"name": item["name"], "problem": "invalid_zarr_metadata", "detail": repr(error)})

    groups = {
        embryo: sorted(movie for movie in by_movie if movie.startswith(f"{embryo}_"))
        for embryo in EMBRYOS
    }
    for embryo, movies in groups.items():
        if len(movies) != MOVIES_PER_EMBRYO:
            problems.append({"embryo": embryo, "problem": "movie_count", "actual": len(movies)})
    for movie, row in by_movie.items():
        if row["zarr_files"] != ZARR_FILES_PER_MOVIE or row["geff_files"] != GEFF_FILES_PER_MOVIE:
            problems.append({"movie": movie, "problem": "component_count", **row})
    if problems:
        raise RuntimeError(json.dumps(problems[:20], indent=2))

    folds: list[dict[str, object]] = []
    trainer_folds: list[dict[str, list[str]]] = []
    for source, target in (("44b6", "6bba"), ("6bba", "44b6")):
        source_movies = [f"{name}.zarr" for name in groups[source]]
        target_movies = [f"{name}.zarr" for name in groups[target]]
        train = source_movies[:10]
        source_validation = source_movies[10:]
        target_development = target_movies[:4]
        target_locked_audit = target_movies[4:]
        folds.append(
            {
                "source_embryo": source,
                "target_embryo": target,
                "train": train,
                "source_checkpoint_validation": source_validation,
                "target_development": target_development,
                "target_locked_audit": target_locked_audit,
            }
        )
        trainer_folds.append({"train": train, "test": source_validation})

    content_hashes = (
        {movie: content_tree_sha256(args.data_root, rows) for movie, rows in sorted(entries_by_movie.items())}
        if args.content_hash
        else None
    )
    integrity = {
        "status": "PASS_OFFICIAL_24_SIZE_AND_STRUCTURE_AUDIT",
        "manifest_path": str(args.manifest),
        "manifest_file_sha256": file_sha256(args.manifest),
        "relevant_manifest_canonical_sha256": canonical_sha256(relevant),
        "data_root": str(args.data_root),
        "file_count": len(relevant),
        "total_bytes": sum(item["size"] for item in relevant),
        "movie_counts": {embryo: len(movies) for embryo, movies in groups.items()},
        "per_movie": by_movie,
        "zarr_metadata_json_files_parsed": metadata_json_files,
        "content_sha256_by_movie": content_hashes,
        "verification_scope": "Every official train file checked for safe unique path, presence and exact manifest byte size; every Zarr metadata JSON parsed and validated as v3; Zarr and GEFF component counts checked independently. Optional content hashes bind names, sizes and bytes.",
        "limitation": "Byte-size agreement is not a cryptographic content hash because the Kaggle manifest exposes names and sizes, not per-file hashes.",
    }
    contract = {
        "status": "FROZEN_OFFICIAL24_PRIVATE_FIRST_SPLIT",
        "purpose": "Compute-matched reciprocal embryo-domain evaluation for model development",
        "integrity": integrity,
        "folds": folds,
        "selection_policy": (
            "Checkpoint selection uses only two source-embryo movies. Up to four target-development "
            "movies may reject a hypothesis. The eight target locked-audit movies are opened once only "
            "after architecture, initialization, threshold and linker policy are frozen."
        ),
        "reporting_policy": (
            "Report both reciprocal folds, pooled sufficient statistics, worst-fold score, per-movie "
            "distribution and paired deltas. Public LB is a runtime/regression check, not the primary selector."
        ),
        "uncertainty_warning": (
            "Movie bootstrap is conditional on two observed embryo domains and cannot estimate unseen-embryo population uncertainty."
        ),
    }
    args.contract_output.parent.mkdir(parents=True, exist_ok=True)
    args.trainer_output.parent.mkdir(parents=True, exist_ok=True)
    args.contract_output.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    args.trainer_output.write_text(json.dumps(trainer_folds, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"contract": str(args.contract_output), "trainer": str(args.trainer_output), **integrity}, indent=2))


if __name__ == "__main__":
    main()
