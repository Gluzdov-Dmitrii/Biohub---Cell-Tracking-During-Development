"""Separate current-organizer-metric EXP234/EXP214 paired target175 rescore.

The complete no-label graph/source/runtime gate is written before any GEFF is
opened. This scorer writes only to a new output directory; it never changes the
historical EXP214-pinned score or its stopped handoff receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

from check_current_organizer_metric_runtime import (
    METRIC_SHA256, ORGANIZER_COMMIT, TRACKSDATA_COMMIT,
    load_metric, synthetic_contract, validate_runtime,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(path: Path, digest: str) -> None:
    assert sha(path) == digest, str(path)


def pinned_manifest(code: Path, digest: str) -> dict:
    path = code / "code_manifest.json"
    pinned(path, digest)
    manifest = json.loads(path.read_text())
    for name, expected in manifest.items():
        file = (code / name).resolve()
        assert file.is_relative_to(code.resolve()) and file.is_file()
        pinned(file, expected)
    return manifest


def load_historical_gate(code: Path):
    path = code / "score_exp234_target_official.py"
    sys.path.insert(0, str(code))
    spec = importlib.util.spec_from_file_location("exp234_historical_graph_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.gate


def image_metadata(cohort: dict) -> list[dict]:
    """Read only image metadata; no image arrays or labels."""
    rows = []
    for name in sorted(cohort):
        movie = cohort[name]
        zarr = Path(movie["zarr"])
        assert zarr.stem == name and zarr.suffix == ".zarr"
        root_path, array_path = zarr / "zarr.json", zarr / "0/zarr.json"
        root = json.loads(root_path.read_text())
        array = json.loads(array_path.read_text())
        assert list(array["shape"]) == movie["shape"]
        attrs = root.get("attributes", {})
        if "multiscales" in attrs:
            transform = attrs["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]
            assert transform["type"] == "scale"
            scale = tuple(float(v) for v in transform["scale"][-3:])
        else:
            scale = (1.625, 0.40625, 0.40625)
        assert len(scale) == 3 and all(math.isfinite(v) and v > 0 for v in scale)
        rows.append({"dataset": name, "zarr_root_sha256": sha(root_path),
                     "zarr_array_sha256": sha(array_path), "scale": scale})
    assert len(rows) == 175
    return rows


def prelabel_gate(config: dict):
    assert config["experiment"] == "EXP234_CURRENT_ORGANIZER_TARGET175_V1"
    assert config["organizer_commit"] == ORGANIZER_COMMIT
    assert config["tracksdata_commit"] == TRACKSDATA_COMMIT
    assert config["metric_sha256"] == METRIC_SHA256
    code = Path(config["code"])
    manifest = pinned_manifest(code, config["code_manifest_sha256"])
    assert manifest["score_exp234_current_organizer.py"] == sha(Path(__file__))
    old_code = Path(config["historical_code"])
    old_manifest = pinned_manifest(old_code, config["historical_manifest_sha256"])
    assert old_manifest["score_exp234_target_official.py"] == config["historical_scorer_sha256"]
    historical_config_path = Path(config["historical_config"])
    pinned(historical_config_path, config["historical_config_sha256"])
    historical_config = json.loads(historical_config_path.read_text())
    pinned(Path(config["historical_gate"]), config["historical_gate_sha256"])
    old_gate = json.loads(Path(config["historical_gate"]).read_text())
    assert old_gate["status"] == "PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS"
    cohort, candidate, baseline_graphs, baseline_rows, _, freshly_checked = (
        load_historical_gate(old_code)(historical_config))
    assert freshly_checked == old_gate
    pinned(Path(config["historical_result"]), config["historical_result_sha256"])
    old_result = json.loads(Path(config["historical_result"]).read_text())
    assert old_result["no_metric_gate_sha256"] == config["historical_gate_sha256"]
    assert old_result["status"] == "PASS_EXP234_SOURCE_SELECTED_TARGET175"
    assert set(candidate) == set(baseline_graphs) == set(cohort)
    assert len(candidate) == 175
    assert len(old_gate["prediction_hashes"]) == 12
    assert len(old_gate["baseline_hashes"]) == 8
    assert old_gate["candidate_count"] == old_gate["baseline_count"] == 175

    # The new metric and exact isolated runtime are pinned before labels open.
    runtime = validate_runtime("remote_py311")
    metric = load_metric(code)
    contract = synthetic_contract(metric)
    images = image_metadata(cohort)
    no_metric = {
        "status": "PASS_EXP234_CURRENT_ORGANIZER_ALL175_BEFORE_LABEL_ACCESS",
        "historical_gate_sha256": config["historical_gate_sha256"],
        "historical_result_sha256": config["historical_result_sha256"],
        "historical_config_sha256": config["historical_config_sha256"],
        "candidate_hashes": old_gate["prediction_hashes"],
        "baseline_hashes": old_gate["baseline_hashes"],
        "candidate_count": 175, "baseline_count": 175,
        "cohort_sha256": historical_config["cohort_sha256"],
        "organizer_commit": ORGANIZER_COMMIT, "metric_sha256": METRIC_SHA256,
        "runtime": runtime, "synthetic_contract": contract,
        "image_metadata": images, "target_labels_read": False,
    }
    return cohort, candidate, baseline_graphs, baseline_rows, old_result, metric, no_metric


def tree_hash(path: Path) -> dict:
    """Hash every GEFF file with relative names after the graph gate."""
    root = path.resolve(strict=True)
    assert root.is_dir()
    files = sorted((p for p in root.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(root).as_posix())
    assert files and (root / "zarr.json").is_file()
    digest = hashlib.sha256()
    total = 0
    for file in files:
        rel = file.relative_to(root).as_posix().encode()
        blob = file.read_bytes()
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        digest.update(len(blob).to_bytes(8, "big"))
        digest.update(hashlib.sha256(blob).digest())
        total += len(blob)
    return {"sha256": digest.hexdigest(), "files": len(files), "bytes": total}


def label_manifest(cohort: dict) -> dict:
    labels = {}
    for name in sorted(cohort):
        zarr = Path(cohort[name]["zarr"])
        path = zarr.with_suffix(".geff")
        assert path.name == name + ".geff"
        labels[name] = tree_hash(path)
    assert len(labels) == 175
    return labels


def to_graph(graph: dict):
    import polars as pl
    import tracksdata as td

    result = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        result.add_node_attr_key(key, pl.Float64, 0.0)
    mapping = {}
    for node in sorted(graph["nodes"]):
        t, z, y, x = graph["nodes"][node]
        mapping[node] = result.add_node({"t": int(t), "z": float(z),
                                         "y": float(y), "x": float(x)})
    for source, target in graph["edges"]:
        result.add_edge(mapping[source], mapping[target], {})
    return result


def score_one(name, graph, gt, scale, estimate, metric):
    pred = to_graph(graph)
    evaluated = metric.evaluate(pred, gt, scale=scale, max_distance=7.0)
    recall = metric.node_recall(pred, gt) if pred.num_nodes() and pred.num_edges() else 0.0
    return {"dataset": name, **metric.per_sample_metrics(evaluated, estimate, recall)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU-only scorer requires hidden CUDA"
    pinned(args.config, args.config_sha256)
    config = json.loads(args.config.read_text())
    assert Path(sys.executable) == Path(config["python"])
    assert sys.prefix != sys.base_prefix, "Scorer requires its isolated metric environment"
    output = Path(config["output"])
    assert output.parent == Path(config["run"]) and not output.exists()
    (cohort, candidate, baseline, baseline_rows, old_result,
     metric, no_metric) = prelabel_gate(config)
    output.mkdir(parents=True, exist_ok=False)
    gate_path = output / "no_metric_gate.json"
    gate_path.write_bytes((json.dumps(no_metric, indent=2) + "\n").encode())

    # Nothing above opens GEFF. The complete graph/source gate is durable now.
    labels_before = label_manifest(cohort)
    label_path = output / "label_tree_hashes.json"
    label_path.write_bytes((json.dumps(labels_before, indent=2) + "\n").encode())
    from geff import GeffMetadata
    import tracksdata as td

    scales = {row["dataset"]: tuple(row["scale"]) for row in no_metric["image_metadata"]}
    old_rows, new_rows = [], []
    candidate_old_rows = {row["dataset"]: row for row in old_result["rows"]}
    assert len(candidate_old_rows) == 175
    for name in sorted(cohort):
        geff = Path(cohort[name]["zarr"]).with_suffix(".geff")
        loaded = td.graph.IndexedRXGraph.from_geff(geff)
        gt = loaded[0] if isinstance(loaded, tuple) else loaded
        estimate = (GeffMetadata.read(geff).extra or {}).get("estimated_number_of_nodes")
        assert estimate is not None and math.isfinite(float(estimate)) and float(estimate) > 0
        old = score_one(name, baseline[name], gt, scales[name], float(estimate), metric)
        new = score_one(name, candidate[name], gt, scales[name], float(estimate), metric)
        assert old["num_pred_nodes"] == baseline_rows[name]["num_pred_nodes"]
        assert new["num_pred_nodes"] == candidate_old_rows[name]["num_pred_nodes"]
        old_rows.append(old)
        new_rows.append(new)
        print(json.dumps({"scored_movie": name}), flush=True)
    assert label_manifest(cohort) == labels_before, "Target GEFF changed during rescore"
    old_summary, new_summary = metric.summarise(old_rows), metric.summarise(new_rows)
    assert old_summary["n"] == new_summary["n"] == 175
    assert math.isfinite(old_summary["score"]) and math.isfinite(new_summary["score"])
    by_embryo = {arm: {prefix: metric.summarise([row for row in rows
                                                 if row["dataset"].startswith(prefix + "_")])
                       for prefix in ("44b6", "6bba")}
                 for arm, rows in (("exp214", old_rows), ("exp234", new_rows))}
    result = {
        "status": "PASS_EXP234_TARGET175_CURRENT_ORGANIZER_METRIC_PAIRED",
        "evidence_class": ("Current organizer metric on fixed EXP234 and EXP214 graphs; "
                           "historically exposed embryo domains, not pristine OOF."),
        "organizer_commit": ORGANIZER_COMMIT, "metric_sha256": METRIC_SHA256,
        "no_metric_gate_sha256": sha(gate_path), "label_tree_hashes_sha256": sha(label_path),
        "baseline_summary": old_summary, "candidate_summary": new_summary,
        "delta_vs_exp214": new_summary["score"] - old_summary["score"],
        "by_embryo": by_embryo, "baseline_rows": old_rows, "candidate_rows": new_rows,
        "kaggle_post": False,
    }
    (output / "result.json").write_bytes((json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"status": result["status"], "score": new_summary["score"],
                      "baseline": old_summary["score"], "delta": result["delta_vs_exp214"]}))


if __name__ == "__main__":
    main()
