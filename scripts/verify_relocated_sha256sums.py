#!/usr/bin/env python3
import argparse
import hashlib
import os
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(manifest: Path, old_root: Path, new_root: Path) -> list[tuple[str, Path]]:
    old_prefix = str(old_root.resolve()) + os.sep
    new_root = new_root.resolve()
    rows: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        parts = raw.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"line {number}: malformed SHA256SUMS row")
        expected, old_path_text = parts
        if any(ch not in "0123456789abcdef" for ch in expected):
            raise ValueError(f"line {number}: invalid SHA-256")
        if not old_path_text.startswith(old_prefix):
            raise ValueError(f"line {number}: path is outside exact old root")
        relative = Path(old_path_text[len(old_prefix):])
        candidate = (new_root / relative).resolve()
        if candidate == new_root or new_root not in candidate.parents:
            raise ValueError(f"line {number}: relocated path escapes new root")
        if candidate in seen:
            raise ValueError(f"line {number}: duplicate relocated path")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        actual = sha256(candidate)
        if actual != expected:
            raise ValueError(f"line {number}: SHA mismatch for {candidate}")
        seen.add(candidate)
        rows.append((expected, candidate))
    if not rows:
        raise ValueError("manifest is empty")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--old-root", type=Path, required=True)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = verify(args.manifest, args.old_root, args.new_root)
    output = args.output.resolve()
    new_root = args.new_root.resolve()
    if output == new_root or new_root not in output.parents:
        raise ValueError("output must be inside new root")
    if output.exists():
        raise FileExistsError(output)
    temporary = output.with_name(output.name + f".tmp.{os.getpid()}")
    temporary.write_text("".join(f"{digest}  {path}\n" for digest, path in rows), encoding="utf-8")
    os.replace(temporary, output)
    print(f"PASS_RELOCATED_SHA256SUMS files={len(rows)} output={output}")


if __name__ == "__main__":
    main()
