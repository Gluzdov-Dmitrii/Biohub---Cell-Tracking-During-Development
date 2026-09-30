"""Safely and resumably extract only frozen manifest files from a Kaggle archive."""
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath


def safe_relative(name: str) -> Path:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or path.parts[0] != "train":
        raise ValueError(f"unsafe archive path: {name!r}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe archive component: {name!r}")
    return Path(*path.parts)


def selected_entries(manifest: dict, holdout: str) -> list[dict]:
    result = []
    for item in manifest["files"]:
        relative = safe_relative(str(item["name"]))
        if relative.parts[1].startswith(holdout + "_"):
            result.append({"name": str(item["name"]), "size": int(item["size"])})
    names = [row["name"] for row in result]
    if len(names) != len(set(names)):
        raise ValueError("duplicate selected manifest path")
    return sorted(result, key=lambda row: row["name"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--holdout", choices=("44b6", "6bba"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    entries = selected_entries(json.loads(args.manifest.read_text(encoding="utf-8")), args.holdout)
    args.destination.mkdir(parents=True, exist_ok=True)
    extracted = skipped = 0
    extracted_bytes = 0
    with zipfile.ZipFile(args.archive) as archive:
        archive_members = {item.filename: item for item in archive.infolist() if not item.is_dir()}
        missing = [row["name"] for row in entries if row["name"] not in archive_members]
        wrong_archive_size = [
            {"name": row["name"], "manifest": row["size"], "archive": archive_members[row["name"]].file_size}
            for row in entries
            if row["name"] in archive_members and archive_members[row["name"]].file_size != row["size"]
        ]
        if missing or wrong_archive_size:
            raise RuntimeError(json.dumps({"missing": missing[:20], "wrong_size": wrong_archive_size[:20]}))
        for index, row in enumerate(entries, 1):
            relative = safe_relative(row["name"])
            target = args.destination / relative
            if target.is_file() and target.stat().st_size == row["size"]:
                skipped += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".partial")
            with archive.open(row["name"]) as source, temporary.open("wb") as sink:
                shutil.copyfileobj(source, sink, length=1024 * 1024)
            if temporary.stat().st_size != row["size"]:
                raise RuntimeError(f"extracted size mismatch: {row['name']}")
            temporary.replace(target)
            extracted += 1
            extracted_bytes += row["size"]
            if index % 250 == 0:
                print(f"processed_files={index}/{len(entries)}", flush=True)
    result = {
        "status": "PASS_SELECTIVE_EXTRACTION",
        "archive": str(args.archive),
        "manifest": str(args.manifest),
        "holdout": args.holdout,
        "files": len(entries),
        "bytes": sum(row["size"] for row in entries),
        "newly_extracted_files": extracted,
        "newly_extracted_bytes": extracted_bytes,
        "already_complete_files": skipped,
        "destination": str(args.destination),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
