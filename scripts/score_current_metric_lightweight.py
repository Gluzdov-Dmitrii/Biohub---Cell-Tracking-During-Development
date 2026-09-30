"""Torch-free, pinned current-metric adapter for reciprocal target scorers."""
import hashlib
import importlib
from importlib import metadata
import json
import math
from pathlib import Path

from check_current_organizer_metric_runtime import synthetic_contract, validate_runtime


IMAGE_AUDIT_SHA = "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_gate(config, metrics_sha, division_sha):
    assert config["tracksdata_commit"] == TRACKSDATA_COMMIT
    assert config["current_metrics_sha256"] == metrics_sha
    assert config["current_division_sha256"] == division_sha
    for key, digest in (("current_metrics", metrics_sha),
                        ("current_division", division_sha)):
        assert sha(config[key]) == digest
    assert Path(config["current_metrics"]).parent == Path(config["current_division"]).parent
    for module_name, path_key in (("current_official.metrics", "current_metrics"),
                                  ("current_official.division_metrics", "current_division")):
        module = importlib.import_module(module_name)
        assert Path(module.__file__).resolve() == Path(config[path_key]).resolve()
    direct = json.loads(metadata.distribution("tracksdata").read_text("direct_url.json"))
    assert direct["vcs_info"]["vcs"] == "git"
    assert direct["vcs_info"]["commit_id"] == TRACKSDATA_COMMIT
    runtime = validate_runtime("remote_py311")
    contract = synthetic_contract(importlib.import_module("current_official.metrics"))
    return runtime, contract


def image_metadata(config, cohort, names):
    assert config["image_scale_audit_sha256"] == IMAGE_AUDIT_SHA
    assert sha(config["image_scale_audit"]) == IMAGE_AUDIT_SHA
    audited = json.loads(Path(config["image_scale_audit"]).read_text())
    assert audited["status"] == "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS"
    reference = {row["dataset"]: row for row in audited["rows"]}
    assert len(reference) == 175
    rows = []
    for name in names:
        zarr = Path(cohort[name]["zarr"])
        assert zarr.name == name + ".zarr"
        root_path, array_path = zarr / "zarr.json", zarr / "0/zarr.json"
        root = json.loads(root_path.read_text())
        array = json.loads(array_path.read_text())
        assert list(array["shape"]) == cohort[name]["shape"]
        attrs = root.get("attributes", {})
        if "multiscales" in attrs:
            transform = attrs["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]
            assert transform["type"] == "scale"
            scale = [float(v) for v in transform["scale"][-3:]]
        else:
            scale = [1.625, 0.40625, 0.40625]
        assert scale == [1.625, 0.40625, 0.40625]
        row = {"dataset": name, "zarr_root_sha256": sha(root_path),
               "zarr_array_sha256": sha(array_path), "scale": scale}
        assert row == reference[name]
        rows.append(row)
    assert len(rows) == len(names) and len({row["dataset"] for row in rows}) == len(names)
    return rows


def build_graph(points, edges):
    """Copy the historical graph constructor without importing torch."""
    import polars as pl
    import tracksdata as td
    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, -999999.0)
    node_ids = graph.bulk_add_nodes([
        {"t": int(t), "z": float(z), "y": float(y), "x": float(x)}
        for t, z, y, x in points])
    if edges:
        graph.add_edge_attr_key("edge_prob", pl.Float64, 0.0)
        graph.add_edge_attr_key("edge_dist", pl.Float64, 0.0)
        graph.bulk_add_edges([
            {"source_id": node_ids[source], "target_id": node_ids[target],
             "edge_prob": prob, "edge_dist": dist}
            for source, target, prob, dist in edges])
    return graph


def label_tree_hash(path):
    root = Path(path).resolve(strict=True)
    assert root.is_dir() and (root / "zarr.json").is_file()
    files = sorted((p for p in root.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(root).as_posix())
    assert files
    digest = hashlib.sha256()
    total = 0
    for file in files:
        relative = file.relative_to(root).as_posix().encode()
        blob = file.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(blob).to_bytes(8, "big"))
        digest.update(hashlib.sha256(blob).digest())
        total += len(blob)
    return {"sha256": digest.hexdigest(), "files": len(files), "bytes": total}


def label_manifest(cohort, names):
    return {name: label_tree_hash(Path(cohort[name]["zarr"]).with_suffix(".geff"))
            for name in sorted(names)}
