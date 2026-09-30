"""Full175 cache/image SHA gate before EXP209 graph reconstruction; no labels."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from run_exp209_reconstruction_chunk_v1 import (
    check_contract, forbid_labels, image_entries, image_tree_sha256,
    require, sha256,
)


def preflight(contract_path: Path, output: Path) -> dict:
    forbid_labels()
    require(os.environ.get("CUDA_VISIBLE_DEVICES", "") in {"", "-1"}, "CUDA must be hidden")
    contract, _historical, manifest = check_contract(contract_path)
    image_pin = json.loads(Path(contract["image_sha_manifest"]).read_text(encoding="utf-8"))
    expected_images = image_pin["image_tree_sha256_by_movie"]
    require(output == Path(contract["run_root"]) / "preflight.json", "preflight output path mismatch")
    require(not output.exists(), "preflight already exists")
    images = {}
    raw_count = gap_count = 0
    for chunk in contract["chunks"]:
        for movie in chunk["movies"]:
            raw = Path(chunk["input_cache_path"][movie])
            require(raw.is_file() and sha256(raw) == chunk["input_cache_sha256"][movie],
                    f"raw candidate SHA mismatch: {movie}")
            raw_count += 1
            if chunk["direction"] == "reverse":
                gap = Path(chunk["gap_cache_path"][movie])
                require(gap.is_file() and sha256(gap) == chunk["gap_cache_sha256"][movie],
                        f"reverse gap SHA mismatch: {movie}")
                gap_count += 1
            images[movie] = image_tree_sha256(Path(contract["data_root"]), movie,
                                               image_entries(manifest, movie))
            require(images[movie] == expected_images[movie], f"image-only SHA pin mismatch: {movie}")
    require(raw_count == len(images) == 175 and gap_count == 59, "full175 input count mismatch")
    result = {"status": "PASS_EXP209_RECONSTRUCTION_INPUTS_NO_LABELS",
              "contract_sha256": sha256(contract_path), "raw_candidate_count": 175,
              "reverse_gap_cache_count": 59, "image_count": 175,
              "image_tree_sha256_by_movie": images,
              "historical_image_manifest_sha256": contract["data_manifest_sha256"],
              "historical_data_audit_sha256": contract["data_audit_sha256"],
              "image_sha_manifest_sha256": contract["image_sha_manifest_sha256"],
              "historical_combined_movie_hashes_recomputed": False,
              "reason": "historical per-movie hashes include GEFF labels; preflight hashes image Zarr only",
              "labels_read": False, "gpu_used": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w",
                   encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = preflight(args.contract, args.output)
    print(json.dumps({key: result[key] for key in ("status", "raw_candidate_count", "reverse_gap_cache_count", "image_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
