"""Build a private Kaggle notebook that packs only missing reciprocal-fold data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "kaggle_notebooks/exp133_private_6bba_pack"


def main() -> None:
    code = r'''import hashlib
import json
import os
import tarfile
from pathlib import Path

MISSING = [
    "6bba_3abfe10a",
    "6bba_784a78c9",
    "6bba_7b5d3b2c",
    "6bba_7d3058ae",
    "6bba_aeee7805",
    "6bba_cff5865f",
]
CHUNK_BYTES = 512 * 1024 * 1024


class ChunkedHashWriter:
    def __init__(self, root: Path):
        self.root = root
        self.index = -1
        self.handle = None
        self.chunk_size = 0
        self.total_size = 0
        self.full_hash = hashlib.sha256()
        self.chunk_hash = None
        self.parts = []
        self._open_next()

    def _open_next(self):
        if self.handle is not None:
            self._finish_current()
        self.index += 1
        self.path = self.root / f"missing_6bba.tar.part{self.index:03d}"
        self.handle = self.path.open("wb")
        self.chunk_hash = hashlib.sha256()
        self.chunk_size = 0

    def _finish_current(self):
        self.handle.close()
        self.parts.append({
            "name": self.path.name,
            "bytes": self.chunk_size,
            "sha256": self.chunk_hash.hexdigest(),
        })

    def write(self, data):
        view = memoryview(data)
        while view:
            capacity = CHUNK_BYTES - self.chunk_size
            piece = view[:capacity]
            self.handle.write(piece)
            self.chunk_hash.update(piece)
            self.full_hash.update(piece)
            count = len(piece)
            self.chunk_size += count
            self.total_size += count
            view = view[count:]
            if self.chunk_size == CHUNK_BYTES:
                self._open_next()
        return len(data)

    def tell(self):
        return self.total_size

    def close(self):
        if self.handle is not None:
            self._finish_current()
            self.handle = None


candidates = [
    Path("/kaggle/input/biohub-cell-tracking-during-development/train"),
    Path("/kaggle/input/competitions/biohub-cell-tracking-during-development/train"),
]
train_root = next((path for path in candidates if path.is_dir()), None)
if train_root is None:
    raise FileNotFoundError(candidates)

sources = []
for stem in MISSING:
    for suffix, expected_count in ((".zarr", 102), (".geff", 21)):
        directory = train_root / f"{stem}{suffix}"
        files = sorted(path for path in directory.rglob("*") if path.is_file())
        if len(files) != expected_count:
            raise RuntimeError(f"{directory}: {len(files)} != {expected_count}")
        for path in files:
            sources.append({
                "relative_path": path.relative_to(train_root).as_posix(),
                "bytes": path.stat().st_size,
            })

output = Path("/kaggle/working/exp133_6bba_pack")
output.mkdir(parents=True, exist_ok=True)
writer = ChunkedHashWriter(output)
try:
    with tarfile.open(fileobj=writer, mode="w|") as archive:
        for row in sources:
            path = train_root / row["relative_path"]
            info = archive.gettarinfo(str(path), arcname=row["relative_path"])
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            with path.open("rb") as handle:
                archive.addfile(info, handle)
finally:
    writer.close()

manifest = {
    "status": "PASS_PRIVATE_DATA_PACK",
    "competition": "biohub-cell-tracking-during-development",
    "missing_stems": MISSING,
    "source_file_count": len(sources),
    "source_bytes": sum(row["bytes"] for row in sources),
    "source_files": sources,
    "tar_bytes": writer.total_size,
    "tar_sha256": writer.full_hash.hexdigest(),
    "chunk_bytes_limit": CHUNK_BYTES,
    "parts": writer.parts,
    "contains_metrics_or_training": False,
}
(output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({key: manifest[key] for key in ("status", "source_file_count", "source_bytes", "tar_bytes", "tar_sha256", "parts")}, indent=2))
'''
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Private transport pack: missing 6bba movies\n",
                    "\n",
                    "Private, Internet-off, CPU-only transport utility. It archives six frozen competition movie pairs; it performs no metric evaluation, training, inference or submission.\n",
                ],
            },
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code.splitlines(keepends=True)},
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data_pack.ipynb").write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    metadata = {
        "id": "dmitriigluzdov/biohub-exp133-private-6bba-pack",
        "title": "Biohub EXP133 Private 6bba Data Pack",
        "code_file": "data_pack.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["biology", "data-integrity", "private-oof"],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": ["biohub-cell-tracking-during-development"],
        "model_sources": [],
        "machine_shape": "None",
    }
    (OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
