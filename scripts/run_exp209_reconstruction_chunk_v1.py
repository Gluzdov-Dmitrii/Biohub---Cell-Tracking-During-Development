"""Label-free CPU reconstruction of one frozen EXP209 graph chunk.

Only prediction caches, image Zarrs and nonlabel metadata are read.  The
original EXP209 final graphs were not retained, so outputs are new graphs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys


EXPERIMENT = "EXP209_CURRENT_METRIC_RECONSTRUCTION_V1"
RUN_NAME = "exp209_current_metric_reconstruction_v1_20260927"
HISTORICAL_RESULT_SHA = "bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c"
ARCHIVE_MANIFEST_SHA = "1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a"
DATA_MANIFEST_SHA = "ddf71e7f5cf52a0da152ef8fe32a8e1ff505e8534184a084b04e2e1b9a673add"
DATA_AUDIT_SHA = "1abde88cb6feea73db1ce78ac6fe0994620e3c74e58bfee46455b691052768de"
FORWARD_SELECTION_SHA = "bd98ebbc70a37912a1307c1f3c7b5cc285ea4d6838e2391423694bd27023fc42"
TRAINER_SHA = {"forward": "296d307f9ff174ce3d3db9bc77b8b12c2674178b8b09598fed129574c4b458a4",
               "reverse": "5eb0c0426c8b2cc5331c4e2ea0b34e79d3caf48e8eef822def89c69da0b11b0b"}
SOURCE_SHA = {
    "evaluate_cached_intensity_centroid_family.py": "36a7fa07f7d87ee0a8052a52c8fed759615cda6f095ae812cd740c06b9e9e942",
    "evaluate_cached_intensity_centroid_refinement.py": "0f812c4b4af24cf8512c59cc1cbda6323e0c17f698f46a3b5621dd011971d04b",
    "evaluate_cached_short_track_family.py": "a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3",
    "evaluate_coordinate_consensus.py": "426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2",
}
COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
CHUNK_SIZES = {**{f"forward_{i:02d}": n for i, n in enumerate((24, 24, 24, 24, 20))},
               **{f"reverse_{i:02d}": n for i, n in enumerate((24, 24, 11))}}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def json_file(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def forbid_labels() -> None:
    """Catch accidental GEFF path operations, including inherited imports."""
    def audit(event, args):
        if event not in {"open", "os.listdir", "os.scandir", "os.stat", "os.remove", "os.rename"} or not args:
            return
        raw = args[0]
        if isinstance(raw, (str, bytes, os.PathLike)):
            parts = Path(os.fsdecode(raw)).parts
            if any(part.lower().endswith(".geff") for part in parts):
                raise PermissionError("EXP209 reconstruction forbids GEFF access")
    sys.addaudithook(audit)


def check_pin(path: Path, expected: str, label: str) -> None:
    require(path.is_file() and sha256(path) == expected, f"{label} SHA mismatch or missing")


def canonical_id(value: str) -> str:
    movie = value.removesuffix(".zarr")
    require(re.fullmatch(r"(?:44b6|6bba)_[0-9a-f]{8}", movie) is not None, "invalid movie ID")
    return movie


def check_contract(contract_path: Path):
    contract = json_file(contract_path)
    require(contract.get("experiment") == EXPERIMENT, "wrong reconstruction contract")
    require(contract.get("historical_result_sha256") == HISTORICAL_RESULT_SHA, "historical result pin changed")
    require(contract.get("archive_manifest_sha256") == ARCHIVE_MANIFEST_SHA, "archive manifest pin changed")
    require(contract.get("data_manifest_sha256") == DATA_MANIFEST_SHA, "image manifest pin changed")
    require(contract.get("data_audit_sha256") == DATA_AUDIT_SHA, "data audit pin changed")
    require(contract.get("frozen_policy") == {
        "forward": {"centroid_radius_zyx": [3, 5, 5], "minimum_length": 8},
        "reverse": {"arm": "EXP191 gap selected edges", "minimum_length": 6}}, "frozen policy changed")
    require(contract.get("source_function_sha256") == SOURCE_SHA, "source function pin map changed")
    require(contract.get("labels_read") is False and contract.get("current_organizer_score") is None,
            "contract already contains label/score state")
    for key, expected in (("historical_result", HISTORICAL_RESULT_SHA),
                          ("archive_manifest", ARCHIVE_MANIFEST_SHA),
                          ("data_manifest", DATA_MANIFEST_SHA), ("data_audit", DATA_AUDIT_SHA)):
        check_pin(Path(contract[key]), expected, key)
    historical = json_file(Path(contract["historical_result"]))
    archive_sha_by_name = {}
    for line in Path(contract["archive_manifest"]).read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \./([^/\\]+)", line)
        require(match is not None, "malformed historical archive manifest")
        archive_sha_by_name[match.group(2)] = match.group(1)
    require(len(archive_sha_by_name) == 38, "historical archive manifest entry count changed")
    selected = {direction: [canonical_id(row["dataset"]) for row in historical["directions"][direction]["selected_rows"]]
                for direction in ("forward", "reverse")}
    require(len(selected["forward"]) == 116 and len(selected["reverse"]) == 59,
            "historical selected cohort count changed")
    require(len(set(selected["forward"] + selected["reverse"])) == 175, "historical selected IDs duplicate")
    require(all(movie.startswith("6bba_") for movie in selected["forward"]) and
            all(movie.startswith("44b6_") for movie in selected["reverse"]), "historical direction mismatch")
    image_pin_path = Path(contract["image_sha_manifest"])
    require(image_pin_path.is_file() and
            sha256(image_pin_path) == contract["image_sha_manifest_sha256"],
            "image-only SHA manifest pin mismatch")
    image_pin = json_file(image_pin_path)
    pinned_images = image_pin["image_tree_sha256_by_movie"]
    require(image_pin.get("movie_count") == 175 and image_pin.get("geff_opened") is False and
            image_pin.get("data_audit_sha256") == DATA_AUDIT_SHA and
            image_pin.get("data_manifest_sha256") == DATA_MANIFEST_SHA and
            set(pinned_images) == set(selected["forward"] + selected["reverse"]) and
            all(re.fullmatch(r"[0-9a-f]{64}", value) for value in pinned_images.values()),
            "image-only SHA manifest provenance/cohort mismatch")
    require(contract.get("forward_source_selection_sha256") == FORWARD_SELECTION_SHA,
            "source-only forward selection pin changed")
    check_pin(Path(contract["forward_source_selection"]), FORWARD_SELECTION_SHA, "source-only forward selection")
    forward_selection = json_file(Path(contract["forward_source_selection"]))
    require(forward_selection.get("status") == "PASS_SOURCE_ONLY_CENTROID_SELECTION" and
            forward_selection.get("selected_arm") == "intensity_centroid_r3_5_5" and
            forward_selection.get("selected_radius_zyx_voxels") == [3, 5, 5] and
            forward_selection.get("movies") == 2, "forward selection was not frozen on source validation")
    for direction, prefix in (("forward", "44b6"), ("reverse", "6bba")):
        trainer = contract["source_trainer_manifests"][direction]
        require(trainer["sha256"] == TRAINER_SHA[direction], "source trainer SHA pin changed")
        check_pin(Path(trainer["path"]), TRAINER_SHA[direction], "source trainer manifest")
        rows = json_file(Path(trainer["path"]))
        split = rows[0 if direction == "forward" else 1]
        source_movies = [canonical_id(value) for value in split["train"] + split["test"]]
        require(len(split["train"]) == 10 and len(split["test"]) == 2 and
                len(set(source_movies)) == 12 and all(value.startswith(prefix + "_") for value in source_movies),
                "source split provenance mismatch")
        require(not set(source_movies).intersection(selected[direction]) and
                all(not movie.startswith(prefix + "_") for movie in selected[direction]),
                "source/target embryo provenance overlap")
    chunks = contract["chunks"]
    require([item["name"] for item in chunks] == list(CHUNK_SIZES), "chunk order/names changed")
    for direction in ("forward", "reverse"):
        actual = [movie for item in chunks if item["direction"] == direction for movie in item["movies"]]
        require(actual == selected[direction], f"{direction} assignment differs from sealed selected rows")
    for item in chunks:
        name, direction, movies = item["name"], item["direction"], item["movies"]
        require(direction in {"forward", "reverse"} and name.startswith(direction + "_"), "chunk direction invalid")
        require(len(movies) == CHUNK_SIZES[name], "chunk size changed")
        require(set(item["input_cache_sha256"]) == set(movies) == set(item["input_cache_path"]),
                "candidate cache map mismatch")
        if direction == "reverse":
            require(set(item["gap_cache_sha256"]) == set(movies) == set(item["gap_cache_path"]),
                    "reverse gap cache map mismatch")
        check_pin(Path(item["movies_json"]), item["movies_json_sha256"], "movies.json")
        assigned = [canonical_id(v) for v in json_file(Path(item["movies_json"]))["target_development"]]
        require(assigned == movies, "movies.json assignment mismatch")
        check_pin(Path(item["historical_chunk_result"]), item["historical_chunk_result_sha256"],
                  "historical chunk result")
        require(item["historical_chunk_result_sha256"] == archive_sha_by_name[f"exp209_{name}.json"],
                "chunk result does not match sealed EXP209 archive")
        chunk_result = json_file(Path(item["historical_chunk_result"]))
        raw_rows = chunk_result["input_cache_manifest"]
        raw_paths = {canonical_id(row["dataset"]): row["path"] for row in raw_rows}
        raw_hashes = {canonical_id(row["dataset"]): row["sha256"] for row in raw_rows}
        require(raw_paths == item["input_cache_path"] and raw_hashes == item["input_cache_sha256"],
                "raw cache path/hash map differs from sealed EXP209 result")
        if direction == "reverse":
            check_pin(Path(item["gap_filtered_result"]), item["gap_filtered_result_sha256"],
                      "reverse gap filtered result")
            gap_rows = json_file(Path(item["gap_filtered_result"]))["input_cache_manifest"]
            gap_paths = {Path(row["path"]).stem: row["path"] for row in gap_rows}
            gap_hashes = {Path(row["path"]).stem: row["sha256"] for row in gap_rows}
            require(gap_paths == item["gap_cache_path"] and gap_hashes == item["gap_cache_sha256"],
                    "gap cache path/hash map differs from pinned EXP192 result")
    audit = json_file(Path(contract["data_audit"]))
    require(audit.get("status") == "PASS_EXP192_DATA_AUDIT" and audit.get("movies") == 175,
            "historical image audit status/count changed")
    require(audit.get("manifest_sha256") == DATA_MANIFEST_SHA and
            set(audit.get("content_sha256_by_movie", {})) == set(selected["forward"] + selected["reverse"]),
            "historical data audit cohort/manifest mismatch")
    manifest = json_file(Path(contract["data_manifest"]))
    require(len(manifest.get("files", [])) == 21525 and manifest["missing"]["movies"] == sorted(selected["forward"] + selected["reverse"]),
            "historical data manifest changed")
    code_dir = Path(contract["code_dir"])
    for name, expected in SOURCE_SHA.items():
        check_pin(code_dir / name, expected, name)
    require(Path(contract["run_root"]).name == RUN_NAME, "run namespace changed")
    return contract, historical, manifest


def image_entries(manifest: dict, movie: str) -> list[tuple[str, int]]:
    prefix = f"train/{movie}.zarr/"
    result = [(row["name"][len(prefix):], int(row["size"])) for row in manifest["files"]
              if row["name"].startswith(prefix)]
    require(result and len(set(name for name, _ in result)) == len(result), f"image manifest missing/duplicate: {movie}")
    return sorted(result)


def image_tree_sha256(data_root: Path, movie: str, entries: list[tuple[str, int]]) -> str:
    """Hash only the image Zarr tree; never visit the sibling GEFF directory."""
    image_dir = data_root / f"{movie}.zarr"
    require(image_dir.is_dir(), f"image Zarr missing: {movie}")
    expected = {name for name, _ in entries}
    actual = {path.relative_to(image_dir).as_posix() for path in image_dir.rglob("*") if path.is_file()}
    require(actual == expected, f"image file list differs from historical manifest: {movie}")
    digest = hashlib.sha256()
    for name, size in entries:
        require(".." not in Path(name).parts and not Path(name).is_absolute(), "unsafe image path")
        path = image_dir / name
        require(path.stat().st_size == size, f"image file size differs from historical manifest: {movie}/{name}")
        digest.update(name.encode("utf-8") + b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1 << 20), b""):
                digest.update(block)
    return digest.hexdigest()


def graph_rows(dataset: str, coords, edges):
    import numpy as np
    coords = np.asarray(coords, dtype=np.float64)
    require(coords.ndim == 2 and coords.shape[1] == 4 and np.isfinite(coords).all(), "invalid graph coordinates")
    rows = []
    for index, (time, z, y, x) in enumerate(coords):
        require(float(time).is_integer() and time >= 0, "invalid node time")
        require(min(z, y, x) >= 0, "negative node coordinate")
        rows.append([len(rows), dataset, "node", index, int(time), repr(float(z)), repr(float(y)), repr(float(x)), -1, -1])
    seen, incoming, outgoing = set(), {}, {}
    for source, target, *_ in edges:
        source, target = int(source), int(target)
        require(0 <= source < len(coords) and 0 <= target < len(coords), "invalid edge endpoint")
        require(int(coords[target, 0]) == int(coords[source, 0]) + 1, "nondirected graph time")
        require((source, target) not in seen, "duplicate graph edge")
        seen.add((source, target))
        incoming[target] = incoming.get(target, 0) + 1
        outgoing[source] = outgoing.get(source, 0) + 1
        require(incoming[target] <= 1 and outgoing[source] <= 2, "invalid parent/branch degree")
        rows.append([len(rows), dataset, "edge", -1, -1, -1, -1, -1, source, target])
    return rows


def reconstruct_one(contract: dict, chunk: dict, movie: str, image_sha: str):
    import numpy as np
    import zarr
    code_dir = Path(contract["code_dir"])
    sys.path.insert(0, str(code_dir))
    from evaluate_cached_intensity_centroid_family import refine_movie_family
    from evaluate_coordinate_consensus import registered_links
    from evaluate_cached_short_track_family import filter_family

    candidate_path = Path(chunk["input_cache_path"][movie])
    candidate_sha = chunk["input_cache_sha256"][movie]
    check_pin(candidate_path, candidate_sha, f"raw candidate {movie}")
    with np.load(candidate_path) as payload:
        coords = payload["coords"].astype(np.float64)
    zarr_path = Path(contract["data_root"]) / f"{movie}.zarr"
    group = zarr.open_group(str(zarr_path), mode="r")
    image = group["0"]
    shape = [int(v) for v in image.shape]
    require(len(shape) == 4 and all(v > 0 for v in shape), "invalid image shape")
    transform = group.attrs["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]
    require(transform["type"] == "scale" and len(transform["scale"]) == 4, "missing image physical scale")
    scale = np.asarray(transform["scale"][1:], dtype=np.float64)
    require(np.isfinite(scale).all() and (scale > 0).all(), "invalid image physical scale")

    gap_sha = None
    if chunk["direction"] == "forward":
        refined, telemetry = refine_movie_family(image, coords, scale, [(3, 5, 5)])
        candidate = refined["intensity_centroid_r3_5_5"]
        edges = registered_links(candidate, scale)
        selected_coords, selected_edges, filter_stats = filter_family(candidate, edges, {}, 8)
        historical_label = "intensity_centroid_r3_5_5"
        historical_telemetry = next(row for row in json_file(Path(chunk["historical_chunk_result"]))["telemetry"]
                                    if canonical_id(row["dataset"]) == movie)
        historical_stats = historical_telemetry["filter_by_arm"][historical_label]
        old_centroid = historical_telemetry["by_arm"][historical_label]
        for key, value in telemetry[historical_label].items():
            require(key in old_centroid and
                    (value == old_centroid[key] if isinstance(value, int) else
                     math.isclose(value, old_centroid[key], rel_tol=0.0, abs_tol=1e-9)),
                    f"centroid telemetry differs from historical run: {movie}/{key}")
    else:
        gap_path = Path(chunk["gap_cache_path"][movie])
        gap_sha = chunk["gap_cache_sha256"][movie]
        check_pin(gap_path, gap_sha, f"reverse gap selected edge {movie}")
        with np.load(gap_path) as payload:
            gap_coords = payload["coords"].astype(np.float64)
            gap_edges = list(zip(payload["edge_source"].astype(int).tolist(),
                                 payload["edge_target"].astype(int).tolist(),
                                 payload["edge_probability"].astype(float).tolist(),
                                 payload["edge_distance"].astype(float).tolist()))
        probabilities = {(int(s), int(t)): float(p) for s, t, p, _ in gap_edges}
        selected_coords, selected_edges, filter_stats = filter_family(gap_coords, gap_edges, probabilities, 6)
        historical_stats = next(row for row in json_file(Path(chunk["gap_filtered_result"]))["telemetry"]
                                if canonical_id(row["dataset"]) == movie)["variants"]["min6"]
    require(filter_stats == historical_stats, f"filter telemetry differs from historical run: {movie}")
    require(len(selected_coords) > 0 and np.isfinite(selected_coords).all(), f"nonfinite/empty graph: {movie}")
    for axis, bound in enumerate(shape):
        require(np.all((selected_coords[:, axis] >= 0) & (selected_coords[:, axis] < bound)),
                f"out-of-bounds graph coordinate: {movie}")
    return selected_coords, selected_edges, shape, candidate_sha, gap_sha


def run(contract_path: Path, chunk_name: str, output: Path) -> None:
    forbid_labels()
    require(os.environ.get("CUDA_VISIBLE_DEVICES", "") in {"", "-1"}, "CUDA must be hidden")
    contract, historical, manifest = check_contract(contract_path)
    chunks = {item["name"]: item for item in contract["chunks"]}
    require(chunk_name in chunks, "unknown frozen chunk")
    chunk = chunks[chunk_name]
    expected_output = Path(contract["run_root"]) / "chunks" / chunk_name / "output"
    require(output == expected_output, "output path differs from new run namespace")
    preflight_path = Path(contract["run_root"]) / "preflight.json"
    preflight = json_file(preflight_path)
    require(preflight["status"] == "PASS_EXP209_RECONSTRUCTION_INPUTS_NO_LABELS" and
            preflight["contract_sha256"] == sha256(contract_path) and
            preflight["labels_read"] is False and
            set(preflight["image_tree_sha256_by_movie"]) == set(movie for item in chunks.values() for movie in item["movies"]),
            "full175 no-label preflight missing")
    output.mkdir(parents=True, exist_ok=False)
    records = []
    historical_rows = {canonical_id(row["dataset"]): row for row in historical["directions"][chunk["direction"]]["selected_rows"]}
    for movie in chunk["movies"]:
        image_sha = image_tree_sha256(Path(contract["data_root"]), movie, image_entries(manifest, movie))
        require(image_sha == preflight["image_tree_sha256_by_movie"][movie], f"image SHA changed after preflight: {movie}")
        coords, edges, shape, cache_sha, gap_sha = reconstruct_one(contract, chunk, movie, image_sha)
        require(len(coords) == historical_rows[movie]["num_pred_nodes"], f"node count differs from historical row: {movie}")
        csv_path = output / f"graph__{movie}.csv"
        with csv_path.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(COLUMNS)
            writer.writerows(graph_rows(movie, coords, edges))
        csv_sha = sha256(csv_path)
        receipt_path = output / f"graph__{movie}.receipt.json"
        receipt = {"dataset": movie, "csv_sha256": csv_sha, "nodes": len(coords), "edges": len(edges),
                   "shape": shape, "input_cache_sha256": cache_sha, "gap_cache_sha256": gap_sha,
                   "image_tree_sha256": image_sha, "labels_read": False,
                   "evidence_class": "new reconstruction from frozen prefinal caches; original final graph hash unavailable"}
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write("\n")
        records.append({"dataset": movie, "csv_sha256": csv_sha, "receipt_sha256": sha256(receipt_path),
                        "nodes": len(coords), "edges": len(edges)})
        print(json.dumps({"reconstructed": movie, "nodes": len(coords), "edges": len(edges)}), flush=True)
    status = {"status": "PASS_EXP209_RECONSTRUCTION_CHUNK_NO_LABELS", "chunk": chunk_name,
              "direction": chunk["direction"], "movies": chunk["movies"], "records": records,
              "labels_read": False, "contract_sha256": sha256(contract_path),
              "preflight_sha256": sha256(preflight_path)}
    with (output / "status.json").open("x", encoding="utf-8") as stream:
        json.dump(status, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--chunk", choices=list(CHUNK_SIZES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.contract, args.chunk, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
