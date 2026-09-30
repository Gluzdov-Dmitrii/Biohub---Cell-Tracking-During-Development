"""Verify the complete eight-chunk EXP192 data-ready transaction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mark_exp192_runs_data_ready import CODE_FILES
from validate_exp192_chunk_structure import sha256


def verify(
    summary_path: Path,
    audit_path: Path,
    chunk_index_path: Path,
    runs_root: Path,
    code_dir: Path,
) -> dict:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(summary, list) or len(summary) != 8:
        raise ValueError("data-ready summary must contain exactly eight rows")

    audit_sha = sha256(audit_path)
    index = json.loads(chunk_index_path.read_text(encoding="utf-8"))
    chunks = list(index.get("chunks", []))
    if len(chunks) != 8:
        raise ValueError("chunk index must contain exactly eight chunks")
    expected_code = {name: sha256(code_dir / name) for name in CODE_FILES}

    expected = {}
    for chunk in chunks:
        direction = str(chunk["direction"])
        number = int(chunk["number"])
        run_id = f"exp192_confirm_{direction}_{number:02d}_20260911"
        expected[run_id] = chunk

    seen = set()
    verified = []
    for row in summary:
        run_id = str(row["run_id"])
        if run_id in seen or run_id not in expected:
            raise ValueError(f"unexpected or duplicate run id: {run_id}")
        seen.add(run_id)
        chunk = expected[run_id]
        receipt_path = runs_root / run_id / "data_ready.json"
        if Path(row["path"]).resolve() != receipt_path.resolve():
            raise ValueError(f"{run_id}: receipt path mismatch")
        if str(row["sha256"]) != sha256(receipt_path):
            raise ValueError(f"{run_id}: summary SHA mismatch")
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        checks = {
            "status": "READY_EXP192_VERIFIED_DATA",
            "run_id": run_id,
            "direction": str(chunk["direction"]),
            "chunk_number": int(chunk["number"]),
            "movies": int(chunk["movies"]),
            "movies_sha256": str(chunk["sha256"]),
            "data_audit_sha256": audit_sha,
            "content_hashed_movies": 175,
            "code_sha256": expected_code,
        }
        for key, value in checks.items():
            if payload.get(key) != value:
                raise ValueError(f"{run_id}: {key} mismatch")
        if (runs_root / run_id / "launch_receipt.txt").exists():
            raise RuntimeError(f"{run_id}: launch receipt predates readiness finalization")
        if (runs_root / run_id / "results" / "SHA256SUMS").exists():
            raise RuntimeError(f"{run_id}: chunk output predates readiness finalization")
        verified.append({"run_id": run_id, "data_ready_sha256": sha256(receipt_path)})

    if seen != set(expected):
        raise ValueError("data-ready summary does not cover the exact chunk index")
    return {
        "status": "PASS_EXP192_DATA_READY_FINALIZATION",
        "chunks": len(verified),
        "data_audit_sha256": audit_sha,
        "chunk_index_sha256": sha256(chunk_index_path),
        "verified": verified,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--chunk-index", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--code-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.summary, args.audit, args.chunk_index, args.runs_root, args.code_dir)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({key: result[key] for key in ("status", "chunks", "data_audit_sha256")}, indent=2))


if __name__ == "__main__":
    main()
