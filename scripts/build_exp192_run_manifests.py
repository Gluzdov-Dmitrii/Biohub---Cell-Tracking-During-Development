"""Create durable run.json records for the eight frozen EXP192 GPU chunks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-index", type=Path, required=True)
    parser.add_argument("--chunks-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-script", type=Path, required=True)
    parser.add_argument("--launch-script", type=Path, required=True)
    args = parser.parse_args()
    index = json.loads(args.chunk_index.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for chunk in index["chunks"]:
        label = f"{chunk['direction']}_{int(chunk['number']):02d}"
        movie_path = args.chunks_dir / f"{label}.json"
        if sha256(movie_path) != chunk["sha256"]:
            raise ValueError(f"chunk hash mismatch: {label}")
        run_id = f"exp192_confirm_{label}_20260911"
        payload = {
            "run_id": run_id,
            "project": "biohub-cell-tracking-during-development",
            "experiment": "EXP192",
            "state": "BLOCKED_DEPENDENCY_DATA",
            "direction": chunk["direction"],
            "chunk_number": int(chunk["number"]),
            "movies": int(chunk["movies"]),
            "movies_sha256": chunk["sha256"],
            "seed": 314159,
            "environment": "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1",
            "data": {
                "path": "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/data/honest195_missing/train",
                "audit_sha256": "PENDING_VERIFIED_STAGE"
            },
            "code": {
                "directory": "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp192_honest195_confirmation_v1_20260911",
                "run_script_sha256": sha256(args.run_script),
                "launch_script_sha256": sha256(args.launch_script)
            },
            "resources": {
                "pool": "quadro",
                "gpu_count": 1,
                "minimum_vram_gib": 12,
                "cpu": 8,
                "ram_gib": 32,
                "peak_run_growth_gib": 5,
                "estimated_minutes": 120
            },
            "anti_adaptation": "Do not inspect scientific outputs until all eight EXP192 chunks complete and merge."
        }
        output = args.output_dir / f"{label}_run.json"
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        outputs.append({"run_id": run_id, "path": str(output), "sha256": sha256(output)})
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
