"""Verify a frozen manifest against a ZIP central directory without extraction."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from extract_manifest_from_archive import safe_relative


def validate(archive_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = []
    for item in manifest["files"]:
        name = str(item["name"])
        safe_relative(name)
        expected.append((name, int(item["size"])))
    names = [name for name, _ in expected]
    if len(names) != len(set(names)):
        raise ValueError("duplicate manifest path")
    with zipfile.ZipFile(archive_path) as archive:
        infos = [item for item in archive.infolist() if not item.is_dir()]
        archive_names = [item.filename for item in infos]
        if len(archive_names) != len(set(archive_names)):
            raise ValueError("duplicate archive member path")
        by_name = {item.filename: item for item in infos}
        missing = [name for name, _ in expected if name not in by_name]
        wrong_size = [
            {"name": name, "expected": size, "actual": by_name[name].file_size}
            for name, size in expected
            if name in by_name and by_name[name].file_size != size
        ]
        if missing or wrong_size:
            raise RuntimeError(json.dumps({"missing": missing[:20], "wrong_size": wrong_size[:20]}))
    return {
        "status": "PASS_ARCHIVE_MANIFEST_CATALOG",
        "archive_bytes": archive_path.stat().st_size,
        "archive_members": len(infos),
        "manifest_files": len(expected),
        "manifest_bytes": sum(size for _, size in expected),
        "missing": 0,
        "wrong_size": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.archive, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
