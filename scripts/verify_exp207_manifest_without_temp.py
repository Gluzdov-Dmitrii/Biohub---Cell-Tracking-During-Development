#!/usr/bin/env python3
"""Fail-closed recovery verifier for EXP207's self-including temp manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(manifest: Path, code_root: Path, gpu_root: Path) -> dict:
    manifest = manifest.resolve(strict=True)
    code_root = code_root.resolve(strict=True)
    gpu_root = gpu_root.resolve(strict=True)
    entries: dict[Path, str] = {}
    for number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = LINE.fullmatch(raw)
        if not match:
            raise ValueError(f"Malformed manifest line {number}")
        path = Path(match.group(2))
        if not path.is_absolute():
            raise ValueError(f"Manifest path is not absolute on line {number}")
        if path in entries:
            raise ValueError(f"Duplicate manifest path: {path}")
        entries[path] = match.group(1)

    expected_temp = manifest.with_name("SHA256SUMS.tmp")
    missing = [path for path in entries if not path.is_file()]
    if missing != [expected_temp]:
        raise ValueError(f"Expected only missing temp entry, got: {missing}")

    verified = 0
    for path, expected in entries.items():
        if path == expected_temp:
            continue
        resolved = path.resolve(strict=True)
        if not (resolved.is_relative_to(code_root) or resolved.is_relative_to(gpu_root)):
            raise ValueError(f"Manifest path escapes frozen roots: {resolved}")
        actual = sha256(resolved)
        if actual != expected:
            raise ValueError(f"SHA mismatch: {resolved}")
        verified += 1

    actual_files = {
        path.resolve(strict=True)
        for root in (code_root, gpu_root)
        for path in root.rglob("*")
        if path.is_file() and path.resolve(strict=True) != manifest
    }
    listed_existing = {path.resolve(strict=True) for path in entries if path != expected_temp}
    if actual_files != listed_existing:
        raise ValueError(
            "Manifest coverage mismatch: "
            f"unlisted={sorted(map(str, actual_files - listed_existing))}, "
            f"noncurrent={sorted(map(str, listed_existing - actual_files))}"
        )

    return {
        "status": "PASS_EXP207_MANIFEST_RECOVERY_WITH_SINGLE_SELF_TEMP_BUG",
        "original_manifest": str(manifest),
        "original_manifest_sha256": sha256(manifest),
        "listed_entries": len(entries),
        "verified_existing_entries": verified,
        "sole_missing_entry": str(expected_temp),
        "exact_current_file_coverage": True,
        "scientific_metrics_opened": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--gpu-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.manifest, args.code_root, args.gpu_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
