"""Build one immutable local-only EXP209 reconstruction v1 staging bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from run_exp209_reconstruction_chunk_v1 import (
    ARCHIVE_MANIFEST_SHA, CHUNK_SIZES, DATA_AUDIT_SHA, DATA_MANIFEST_SHA,
    EXPERIMENT, HISTORICAL_RESULT_SHA, RUN_NAME, SOURCE_SHA, canonical_id,
    require, sha256,
)


REMOTE_ROOT = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE_NAME = RUN_NAME
LOCAL_WORK = Path("work/exp209_current_metric_reconstruction_v1_local_20260927")
ARCHIVE = Path("outputs/research/exp209_selected_centroid_confirmation_20260912")
GAP_SHA = {
    "reverse_00": "ead5422db13c823013e0f070a3e1f148e990afcdb213b057043eeb30f95067b2",
    "reverse_01": "288bbc330373c7807f7e79df06f05f27ea32ea73f7a1166670b222cab035a6f7",
    "reverse_02": "fc8670f827f4a4bfc3eab4a53ca0d649431572be182e1a23d853508baa66a82c",
}
FORWARD_SOURCE_SELECTION = Path("outputs/research/exp208_source_centroid_family_20260911/results/forward_selection.json")
FORWARD_SELECTION_SHA = "bd98ebbc70a37912a1307c1f3c7b5cc285ea4d6838e2391423694bd27023fc42"
TRAINER_MANIFESTS = {
    "forward": (Path("outputs/research/exp130_official24_private_first/trainer_44b6_source.json"),
                "296d307f9ff174ce3d3db9bc77b8b12c2674178b8b09598fed129574c4b458a4"),
    "reverse": (Path("outputs/research/exp130_official24_private_first/exp137_remote_artifacts/trainer_6bba_source.json"),
                "5eb0c0426c8b2cc5331c4e2ea0b34e79d3caf48e8eef822def89c69da0b11b0b"),
}


def bundled_contract(root: Path, bundle: Path) -> dict:
    code = f"{REMOTE_ROOT}/code/{CODE_NAME}"
    run = f"{REMOTE_ROOT}/runs/{RUN_NAME}"
    archive = root / ARCHIVE
    require(sha256(archive / "SHA256SUMS") == ARCHIVE_MANIFEST_SHA, "EXP209 archive manifest pin mismatch")
    require(sha256(archive / "forward_plus_exp191_confirmation.json") == HISTORICAL_RESULT_SHA,
            "EXP209 historical result pin mismatch")
    manifest_hashes = {}
    for line in (archive / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ./")
        manifest_hashes[name] = digest
    require(len(manifest_hashes) == 38, "EXP209 archive count mismatch")
    local = root / LOCAL_WORK
    require(sha256(local / "historical_data_audit.json") == DATA_AUDIT_SHA, "data audit pin mismatch")
    require(sha256(local / "historical_data_manifest.json") == DATA_MANIFEST_SHA, "data manifest pin mismatch")
    image_pin = local / "image_tree_sha256_by_movie_20260927.json"
    require(image_pin.is_file(), "read-only 175-image SHA pin manifest missing")
    pinned_images = json.loads(image_pin.read_text(encoding="utf-8"))
    require(pinned_images.get("movie_count") == 175 and pinned_images.get("geff_opened") is False and
            pinned_images.get("data_audit_sha256") == DATA_AUDIT_SHA and
            pinned_images.get("data_manifest_sha256") == DATA_MANIFEST_SHA,
            "image-only pin manifest provenance mismatch")
    selected = json.loads((archive / "forward_plus_exp191_confirmation.json").read_text(encoding="utf-8"))
    selected_ids = {direction: [canonical_id(row["dataset"]) for row in selected["directions"][direction]["selected_rows"]]
                    for direction in ("forward", "reverse")}
    require(set(pinned_images["image_tree_sha256_by_movie"]) ==
            set(selected_ids["forward"] + selected_ids["reverse"]), "image-only SHA cohort mismatch")
    chunks = []
    for name, size in CHUNK_SIZES.items():
        direction = name.split("_")[0]
        historical_name = f"exp209_{name}.json"
        historical_path = archive / historical_name
        require(sha256(historical_path) == manifest_hashes[historical_name], "historical chunk SHA mismatch")
        historical = json.loads(historical_path.read_text(encoding="utf-8"))
        source_rows = historical["input_cache_manifest"]
        movies = [canonical_id(row["dataset"]) for row in source_rows]
        require(len(movies) == size, "historical chunk size mismatch")
        movie_file = local / f"{name}_movies.json"
        require(sha256(movie_file) == historical["movies_source_sha256"], "movie list SHA mismatch")
        assigned = [canonical_id(value) for value in json.loads(movie_file.read_text(encoding="utf-8"))["target_development"]]
        require(assigned == movies, "movie list differs from historical candidate cache order")
        item = {
            "name": name, "direction": direction, "movies": movies,
            "movies_json": f"{code}/{name}_movies.json",
            "movies_json_sha256": sha256(movie_file),
            "historical_chunk_result": f"{code}/{historical_name}",
            "historical_chunk_result_sha256": manifest_hashes[historical_name],
            "input_cache_path": {canonical_id(row["dataset"]): row["path"] for row in source_rows},
            "input_cache_sha256": {canonical_id(row["dataset"]): row["sha256"] for row in source_rows},
        }
        if direction == "reverse":
            gap_file = local / f"{name}_gap_filtered.json"
            require(sha256(gap_file) == GAP_SHA[name], "reverse gap result SHA mismatch")
            gap_rows = json.loads(gap_file.read_text(encoding="utf-8"))["input_cache_manifest"]
            item.update({
                "gap_filtered_result": f"{code}/{name}_gap_filtered.json",
                "gap_filtered_result_sha256": GAP_SHA[name],
                "gap_cache_path": {Path(row["path"]).stem: row["path"] for row in gap_rows},
                "gap_cache_sha256": {Path(row["path"]).stem: row["sha256"] for row in gap_rows},
            })
            require(set(item["gap_cache_sha256"]) == set(movies), "gap cache cohort mismatch")
        chunks.append(item)
    for direction in ("forward", "reverse"):
        require([movie for item in chunks if item["direction"] == direction for movie in item["movies"]]
                == selected_ids[direction], "frozen selected cohort order mismatch")
    return {
        "experiment": EXPERIMENT,
        "evidence_class": "new reconstruction from historical prefinal inputs; original final graph hashes unavailable",
        "historical_result": f"{code}/historical_result.json",
        "historical_result_sha256": HISTORICAL_RESULT_SHA,
        "archive_manifest": f"{code}/SHA256SUMS",
        "archive_manifest_sha256": ARCHIVE_MANIFEST_SHA,
        "data_manifest": f"{code}/historical_data_manifest.json",
        "data_manifest_sha256": DATA_MANIFEST_SHA,
        "data_audit": f"{code}/historical_data_audit.json",
        "data_audit_sha256": DATA_AUDIT_SHA,
        "image_sha_manifest": f"{code}/image_tree_sha256_by_movie.json",
        "image_sha_manifest_sha256": sha256(image_pin),
        "data_root": f"{REMOTE_ROOT}/data/honest195_missing/train",
        "code_dir": code, "run_root": run,
        "source_function_sha256": SOURCE_SHA,
        "forward_source_selection": f"{code}/forward_source_selection.json",
        "forward_source_selection_sha256": FORWARD_SELECTION_SHA,
        "source_trainer_manifests": {
            direction: {"path": f"{code}/{direction}_source_trainer.json", "sha256": digest}
            for direction, (_path, digest) in TRAINER_MANIFESTS.items()
        },
        "reference_graph_builder_sha256": "f698f97c6b00ec92e41aec032bf24d317d565d4f14bab56610f7d4697c441d70",
        "frozen_policy": {"forward": {"centroid_radius_zyx": [3, 5, 5], "minimum_length": 8},
                          "reverse": {"arm": "EXP191 gap selected edges", "minimum_length": 6}},
        "chunks": chunks,
        "labels_read": False,
        "current_organizer_score": None,
    }


def prepare(root: Path, extra_scripts: list[str]) -> dict:
    root = root.resolve()
    bundle = root / LOCAL_WORK / "bundle"
    bundle.mkdir(parents=True, exist_ok=False)
    copies = {
        "historical_result.json": root / ARCHIVE / "forward_plus_exp191_confirmation.json",
        "SHA256SUMS": root / ARCHIVE / "SHA256SUMS",
        "historical_data_audit.json": root / LOCAL_WORK / "historical_data_audit.json",
        "historical_data_manifest.json": root / LOCAL_WORK / "historical_data_manifest.json",
        "image_tree_sha256_by_movie.json": root / LOCAL_WORK / "image_tree_sha256_by_movie_20260927.json",
        "forward_source_selection.json": root / FORWARD_SOURCE_SELECTION,
    }
    require(sha256(root / FORWARD_SOURCE_SELECTION) == FORWARD_SELECTION_SHA, "source-only forward selection pin mismatch")
    for direction, (path, digest) in TRAINER_MANIFESTS.items():
        require(sha256(root / path) == digest, f"{direction} source trainer manifest pin mismatch")
        copies[f"{direction}_source_trainer.json"] = root / path
    for name in CHUNK_SIZES:
        copies[f"{name}_movies.json"] = root / LOCAL_WORK / f"{name}_movies.json"
        copies[f"exp209_{name}.json"] = root / ARCHIVE / f"exp209_{name}.json"
        if name.startswith("reverse_"):
            copies[f"{name}_gap_filtered.json"] = root / LOCAL_WORK / f"{name}_gap_filtered.json"
    for name, digest in SOURCE_SHA.items():
        path = root / "scripts" / name
        require(sha256(path) == digest, f"source function changed: {name}")
        copies[name] = path
    for script_name in extra_scripts:
        copies[script_name] = root / "scripts" / script_name
    for name, source in copies.items():
        require(source.is_file(), f"missing bundle source: {source}")
        shutil.copyfile(source, bundle / name)
    contract = bundled_contract(root, bundle)
    (bundle / "contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    entries = [{"name": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
               for path in sorted(bundle.iterdir()) if path.is_file()]
    (bundle / "bundle_manifest.json").write_text(json.dumps({"experiment": EXPERIMENT, "files": entries}, indent=2) + "\n",
                                                  encoding="utf-8")
    return {"bundle": str(bundle), "bundle_manifest_sha256": sha256(bundle / "bundle_manifest.json"),
            "files": len(entries), "contract_sha256": sha256(bundle / "contract.json")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = prepare(args.root, ["run_exp209_reconstruction_chunk_v1.py",
                                 "preflight_exp209_reconstruction_v1.py",
                                 "supervise_exp209_reconstruction_v1.py",
                                 "verify_exp209_reconstruction_graphs_v1.py"])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
