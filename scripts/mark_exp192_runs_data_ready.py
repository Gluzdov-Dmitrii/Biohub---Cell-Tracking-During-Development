"""Atomically mark all EXP192 chunk runs ready after the exact data audit passes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_exp192_chunk_structure import sha256


EXPECTED_AUDIT = {
    "status": "PASS_EXP192_DATA_AUDIT",
    "files": 21525,
    "bytes": 75045173746,
    "movies": 175,
    "movie_counts": {"44b6": 59, "6bba": 116},
    "zarr_metadata_json_files_parsed": 2975,
}

CODE_FILES = [
    "run_exp192_confirmation_chunk.sh",
    "launch_exp192_chunk_remote.sh",
    "validate_exp192_chunk_structure.py",
    "evaluate_cached_fixed_local_flow.py",
    "evaluate_cached_local_flow_linker.py",
    "evaluate_cached_coherent_motion_linker.py",
    "evaluate_coordinate_consensus.py",
]


def mark(audit_path: Path, chunk_index_path: Path, runs_root: Path, code_dir: Path) -> list[dict]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    for key, expected in EXPECTED_AUDIT.items():
        if audit.get(key) != expected:
            raise ValueError(f"data audit {key} mismatch")
    content_hashes = audit.get("content_sha256_by_movie")
    if not isinstance(content_hashes, dict) or len(content_hashes) != 175:
        raise ValueError("full 175-movie content hashes are required")
    audit_sha = sha256(audit_path)
    code_hashes = {name: sha256(code_dir / name) for name in CODE_FILES}
    index = json.loads(chunk_index_path.read_text(encoding="utf-8"))
    chunks = list(index["chunks"])
    if len(chunks) != 8:
        raise ValueError("expected eight chunks")

    prepared = []
    for chunk in chunks:
        direction = str(chunk["direction"])
        number = int(chunk["number"])
        label = f"{direction}_{number:02d}"
        run_id = f"exp192_confirm_{label}_20260911"
        run_dir = runs_root / run_id
        movies_path = run_dir / "movies.json"
        if sha256(movies_path) != chunk["sha256"]:
            raise ValueError(f"{run_id}: movies hash mismatch")
        output = run_dir / "data_ready.json"
        if output.exists():
            raise FileExistsError(output)
        if (run_dir / "launch_receipt.txt").exists() or (run_dir / "results" / "SHA256SUMS").exists():
            raise RuntimeError(f"{run_id}: launch/output exists before data readiness")
        payload = {
            "status": "READY_EXP192_VERIFIED_DATA",
            "run_id": run_id,
            "direction": direction,
            "chunk_number": number,
            "movies": int(chunk["movies"]),
            "movies_sha256": str(chunk["sha256"]),
            "data_audit_path": str(audit_path),
            "data_audit_sha256": audit_sha,
            "manifest_sha256": audit["manifest_sha256"],
            "content_hashed_movies": len(content_hashes),
            "code_sha256": code_hashes,
            "anti_adaptation": "No scientific metric has been opened; models, parameters and promotion gates remain frozen.",
        }
        prepared.append((output, payload))
    results = []
    for output, payload in prepared:
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output)
        results.append({"path": str(output), "sha256": sha256(output), "run_id": payload["run_id"]})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--chunk-index", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--code-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(mark(args.audit, args.chunk_index, args.runs_root, args.code_dir), indent=2))


if __name__ == "__main__":
    main()
