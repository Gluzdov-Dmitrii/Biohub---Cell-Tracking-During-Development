"""Local-only contract and reconstruction tests; no GEFF or remote jobs."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import zarr


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_exp209_reconstruction_v1_local as prepare
import run_exp209_reconstruction_chunk_v1 as runner
import stage_exp209_reconstruction_v1 as stage
import launch_exp209_reconstruction_v1 as launch
from evaluate_cached_intensity_centroid_family import refine_movie_family
from evaluate_cached_short_track_family import filter_family
from evaluate_coordinate_consensus import registered_links


def local_contract(tmp_path):
    contract = prepare.bundled_contract(ROOT, tmp_path)
    work = ROOT / prepare.LOCAL_WORK
    archive = ROOT / prepare.ARCHIVE
    contract.update({
        "historical_result": str(archive / "forward_plus_exp191_confirmation.json"),
        "archive_manifest": str(archive / "SHA256SUMS"),
        "data_manifest": str(work / "historical_data_manifest.json"),
        "data_audit": str(work / "historical_data_audit.json"),
        "image_sha_manifest": str(work / "image_tree_sha256_by_movie_20260927.json"),
        "forward_source_selection": str(ROOT / prepare.FORWARD_SOURCE_SELECTION),
        "code_dir": str(ROOT / "scripts"),
        "run_root": str(tmp_path / runner.RUN_NAME),
    })
    for direction, (relative, _digest) in prepare.TRAINER_MANIFESTS.items():
        contract["source_trainer_manifests"][direction]["path"] = str(ROOT / relative)
    for chunk in contract["chunks"]:
        name = chunk["name"]
        chunk["movies_json"] = str(work / f"{name}_movies.json")
        chunk["historical_chunk_result"] = str(archive / f"exp209_{name}.json")
        if chunk["direction"] == "reverse":
            chunk["gap_filtered_result"] = str(work / f"{name}_gap_filtered.json")
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return path, contract


def test_original_metadata_contract_and_exact_175_assignment(tmp_path):
    path, _contract = local_contract(tmp_path)
    checked, historical, manifest = runner.check_contract(path)
    assert [len(chunk["movies"]) for chunk in checked["chunks"]] == [24, 24, 24, 24, 20, 24, 24, 11]
    assert len(manifest["files"]) == 21525
    assert historical["combined"]["frozen_selected"]["score"] == pytest.approx(0.6815218332750073)
    assert checked["current_organizer_score"] is None


def test_original_contract_cache_tamper_rejected(tmp_path):
    _path, contract = local_contract(tmp_path)
    first = contract["chunks"][0]
    first["input_cache_sha256"][first["movies"][0]] = "0" * 64
    path = tmp_path / "tampered_contract.json"
    path.write_text(json.dumps(contract))
    with pytest.raises(RuntimeError, match="raw cache path/hash map"):
        runner.check_contract(path)


def test_image_hash_reads_exact_image_tree_only(tmp_path):
    data = tmp_path / "data"
    movie = "6bba_00000001"
    image = data / f"{movie}.zarr"
    image.mkdir(parents=True)
    (image / "zarr.json").write_bytes(b"image-metadata")
    (image / "0").mkdir()
    (image / "0" / "part").write_bytes(b"image-pixels")
    label = data / f"{movie}.geff"
    label.mkdir()
    (label / "labels").write_bytes(b"not-touched")
    entries = [("0/part", 12), ("zarr.json", 14)]
    digest = runner.image_tree_sha256(data, movie, entries)
    assert len(digest) == 64
    (image / "0" / "part").write_bytes(b"tampered-data")
    with pytest.raises(RuntimeError, match="image file size"):
        runner.image_tree_sha256(data, movie, entries)


def test_forward_and_reverse_use_frozen_original_functions(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    for movie in ("6bba_00000001", "44b6_00000001"):
        group = zarr.open_group(str(data / f"{movie}.zarr"), mode="w")
        group.create_array("0", data=np.ones((2, 3, 3, 3), dtype=np.uint8))
        group.attrs["multiscales"] = [{"datasets": [{"coordinateTransformations": [
            {"type": "scale", "scale": [1.0, 1.0, 1.0, 1.0]}]}]}]
    coords = np.asarray([[0., 1., 1., 1.], [1., 1., 1., 1.]])
    raw = tmp_path / "raw.npz"
    np.savez(raw, coords=coords)
    raw_sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    image = zarr.open_group(str(data / "6bba_00000001.zarr"), mode="r")["0"]
    refined, telemetry = refine_movie_family(image, coords, np.ones(3), [(3, 5, 5)])
    linked = registered_links(refined["intensity_centroid_r3_5_5"], np.ones(3))
    _fc, _fe, filter_stats = filter_family(refined["intensity_centroid_r3_5_5"], linked, {}, 8)
    history = tmp_path / "forward_history.json"
    history.write_text(json.dumps({"telemetry": [{"dataset": "6bba_00000001.zarr",
        "by_arm": {"intensity_centroid_r3_5_5": telemetry["intensity_centroid_r3_5_5"]},
        "filter_by_arm": {"intensity_centroid_r3_5_5": filter_stats}}]}))
    contract = {"code_dir": str(ROOT / "scripts"), "data_root": str(data)}
    forward = {"direction": "forward", "input_cache_path": {"6bba_00000001": str(raw)},
               "input_cache_sha256": {"6bba_00000001": raw_sha},
               "historical_chunk_result": str(history)}
    nodes, edges, shape, seen_sha, gap_sha = runner.reconstruct_one(contract, forward, "6bba_00000001", "a" * 64)
    assert len(nodes) == 2 and len(edges) == 1 and shape == [2, 3, 3, 3]
    assert seen_sha == raw_sha and gap_sha is None
    assert len(runner.graph_rows("6bba_00000001", nodes, edges)) == 3

    gap = tmp_path / "gap.npz"
    np.savez(gap, coords=coords, edge_source=np.asarray([0]), edge_target=np.asarray([1]),
             edge_probability=np.asarray([0.9]), edge_distance=np.asarray([1.0]))
    gap_sha_expected = hashlib.sha256(gap.read_bytes()).hexdigest()
    _rc, _re, reverse_stats = filter_family(coords, [(0, 1, 0.9, 1.0)], {(0, 1): 0.9}, 6)
    reverse_history = tmp_path / "reverse_history.json"
    reverse_history.write_text(json.dumps({"telemetry": [{"dataset": "44b6_00000001.zarr",
        "variants": {"min6": reverse_stats}}]}))
    reverse = {"direction": "reverse", "input_cache_path": {"44b6_00000001": str(raw)},
               "input_cache_sha256": {"44b6_00000001": raw_sha},
               "gap_cache_path": {"44b6_00000001": str(gap)},
               "gap_cache_sha256": {"44b6_00000001": gap_sha_expected},
               "gap_filtered_result": str(reverse_history)}
    nodes, edges, shape, _cache_sha, gap_sha = runner.reconstruct_one(contract, reverse, "44b6_00000001", "b" * 64)
    assert len(nodes) == 2 and len(edges) == 1 and shape == [2, 3, 3, 3]
    assert gap_sha == gap_sha_expected


def test_graph_rows_reject_bad_direction_and_nonfinite():
    coords = np.asarray([[0., 1., 1., 1.], [1., 1., 1., 1.]])
    with pytest.raises(RuntimeError, match="nondirected"):
        runner.graph_rows("6bba_00000001", coords, [(1, 0, 1., 0.)])
    coords[0, 1] = np.nan
    with pytest.raises(RuntimeError, match="invalid graph coordinates"):
        runner.graph_rows("6bba_00000001", coords, [])


def test_stage_and_launch_remote_programs_are_review_gated_and_one_shot():
    stage_source = stage.remote_stage_program(b"dummy", "a" * 64,
        prepare.REMOTE_ROOT + "/code/" + prepare.CODE_NAME)
    launch_source = launch.remote_launch_program(
        prepare.REMOTE_ROOT + "/code/" + prepare.CODE_NAME,
        prepare.REMOTE_ROOT + "/runs/" + prepare.CODE_NAME,
        "a" * 64, "b" * 64)
    ast.parse(stage_source)
    ast.parse(launch_source)
    assert "not target.exists()" in stage_source and "target.mkdir" in stage_source
    assert "not run.exists()" in launch_source and "run.mkdir" in launch_source
    assert "CUDA_VISIBLE_DEVICES':'','" in launch_source
