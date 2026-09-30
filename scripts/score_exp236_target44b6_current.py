"""Guarded EXP236 target44b6 score; open labels only after all 59 graphs pass.

The source6bba epoch10 checkpoint was sealed before this rollout. The target
evaluation is embryo-disjoint in model training/selection, but these embryo
labels were historically exposed elsewhere in the research program.
"""
import argparse
import hashlib
import importlib
from importlib import metadata
import json
import math
from pathlib import Path
import subprocess
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, rows_close, score_one
from check_current_organizer_metric_runtime import synthetic_contract, validate_runtime


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
QUEUE = "/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
PREREG_SHA = "a36787c0187284e07f465097153a30575c4a5ef722e4d627b955084eb1b8c400"
TRAINING_SHA = "266732c9cbbaea76a45ad9a4706b3b025b11d36be0762b00f0838c0d8b8efcdb"
HANDOFF_SHA = "9d8c37c1d3b1d14e2e7589704d3899b678f2398cd16f120d89c09e3e16d9ba07"
SOURCE_SCORE_SHA = "5b0e87506e6d95a7c8175825b9a122292ee664fa71bc7994e507969b81ac4737"
SOURCE_PLAN_SHA = "3633711ba0a3706be43c71907261afa5904db93d26cb1b29fb3dc19294474421"
PARENT_MANIFEST_SHA = "92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2"
CHECKPOINT_SHA = "d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"
BASELINE_SHA = "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5"
CURRENT_METRICS_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
CURRENT_DIVISION_SHA = "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
IMAGE_AUDIT_SHA = "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, digest):
    assert sha(path) == digest, str(path)


def state_digest(value):
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def live_queue():
    result = subprocess.run(["python3", QUEUE, "status"], capture_output=True, text=True,
                            check=True, timeout=30)
    return json.loads(result.stdout)


def checked_graph(path, name, shape, expected_nodes=None, expected_edges=None):
    graphs = read_graphs(path)
    assert set(graphs) == {name}, (path, set(graphs))
    graph = graphs[name]
    if expected_nodes is not None:
        assert len(graph["nodes"]) == expected_nodes
    if expected_edges is not None:
        assert len(graph["edges"]) == expected_edges
    assert len(shape) == 4 and all(isinstance(n, int) and n > 0 for n in shape)
    for point in graph["nodes"].values():
        assert len(point) == len(shape)
        assert all(math.isfinite(float(value)) and float(value) == int(value)
                   and 0 <= value < limit for value, limit in zip(point, shape)), name
    return graph


def _manifest(code, digest):
    pinned(code / "code_manifest.json", digest)
    files = json.loads((code / "code_manifest.json").read_text())
    assert isinstance(files, dict) and files
    for name, item_sha in files.items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve()) and path.is_file()
        pinned(path, item_sha)


def live_group_dead(pgid):
    """A fresh Linux process-group check, allowing only exited zombies."""
    assert isinstance(pgid, int) and pgid > 0
    for stat in Path("/proc").glob("[0-9]*/stat"):
        try:
            raw = stat.read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            if len(fields) > 2 and fields[0] != "Z" and int(fields[2]) == pgid:
                return False
        except (FileNotFoundError, ProcessLookupError):
            continue
    return True


def current_import_gate(config):
    """Fail before label access if the pinned current evaluator cannot import."""
    for module_name, path_key in (("current_official.metrics", "current_metrics"),
                                  ("current_official.division_metrics", "current_division")):
        module = importlib.import_module(module_name)
        assert Path(module.__file__).resolve() == Path(config[path_key]).resolve()
    installed = metadata.distribution("tracksdata")
    direct_url = json.loads(installed.read_text("direct_url.json"))
    assert direct_url["vcs_info"]["vcs"] == "git"
    assert direct_url["vcs_info"]["commit_id"] == TRACKSDATA_COMMIT
    runtime = validate_runtime("remote_py311")
    contract = synthetic_contract(importlib.import_module("current_official.metrics"))
    return runtime, contract


def image_metadata(config, cohort, names):
    """Pin target image scale without opening image arrays or GEFF labels."""
    pinned(config["image_scale_audit"], IMAGE_AUDIT_SHA)
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
    assert len(rows) == 59
    return rows


def label_tree_hash(path):
    """Hash GEFF bytes only after the durable no-label gate exists."""
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


def _baseline(config, cohort):
    pinned(config["baseline_metrics"], config["baseline_metrics_sha256"])
    baseline = json.loads(Path(config["baseline_metrics"]).read_text())
    assert baseline["status"] == "PASS_HONEST_PAIRED_CV"
    assert abs(baseline["summary"]["public"]["score"] - 0.7427291486246141) <= 1e-12
    rows = baseline["rows"]["public"]
    baseline_rows = {row["dataset"]: row for row in rows}
    assert len(rows) == len(baseline_rows) == 175 and set(baseline_rows) == set(cohort)
    target_rows = [row for row in rows if row["dataset"] in set(config["target_ids"])]
    assert len(target_rows) == 59
    target_rows_sha = hashlib.sha256(json.dumps(target_rows, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    assert target_rows_sha == config["baseline_target_rows_sha256"]
    old = {}
    hashes = []
    for part in baseline["input_hashes"]["public"]:
        csv_path = Path(part["csv"])
        pinned(csv_path, part["sha256"])
        receipt_path = csv_path.parent / "inference_receipt.json"
        pinned(receipt_path, part["receipt_sha256"])
        receipt = json.loads(receipt_path.read_text())
        assert receipt["submission_sha256"] == part["sha256"]
        graphs = read_graphs(csv_path)
        assert set(graphs) == set(receipt["movies"])
        assert not set(old).intersection(graphs)
        old.update(graphs)
        hashes.append(part)
    assert len(hashes) == 8 and set(old) == set(cohort)
    assert hashes == config["baseline_input_hashes"]
    assert len([part for part in hashes if "_44b6_" in part["csv"]]) == 5
    assert set(config["target_ids"]) <= set(old)
    return {name: old[name] for name in config["target_ids"]}, baseline_rows, baseline, hashes


def gate(config, queue_state=None):
    """All checks here are label-free. This function never touches GEFF paths."""
    assert config["experiment"] == "EXP236_SOURCE6BBA_TARGET44B6_CURRENT59"
    assert config["evidence_class"] == "leakage-controlled reciprocal evaluation; historically exposed target labels"
    assert config["assignment_sha256"] == ASSIGNMENT_SHA
    assert config["prereg_sha256"] == PREREG_SHA
    assert config["source_training_sha256"] == TRAINING_SHA
    assert config["source_handoff_sha256"] == HANDOFF_SHA
    assert config["source_score_sha256"] == SOURCE_SCORE_SHA
    assert config["source_graph_plan_sha256"] == SOURCE_PLAN_SHA
    assert config["parent_graph_manifest_sha256"] == PARENT_MANIFEST_SHA
    assert config["checkpoint_sha256"] == CHECKPOINT_SHA
    assert config["cohort_sha256"] == COHORT_SHA
    assert config["baseline_metrics_sha256"] == BASELINE_SHA
    assert config["current_metrics_sha256"] == CURRENT_METRICS_SHA
    assert config["current_division_sha256"] == CURRENT_DIVISION_SHA
    assert config["tracksdata_commit"] == TRACKSDATA_COMMIT
    assert config["image_scale_audit_sha256"] == IMAGE_AUDIT_SHA
    assert Path(sys.executable).resolve() == Path(config["python"]).resolve()
    assert sys.prefix != sys.base_prefix
    pinned(config["current_metrics"], CURRENT_METRICS_SHA)
    pinned(config["current_division"], CURRENT_DIVISION_SHA)
    assert Path(config["current_metrics"]).parent == Path(config["current_division"]).parent
    pinned(config["assignment"], ASSIGNMENT_SHA)
    assignment = json.loads(Path(config["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["target_labels_read"] is False and assignment["thresholds_selected"] is False
    chunks = assignment["directions"]["6bba"]["chunks"]
    assert assignment["directions"]["6bba"]["target_embryo"] == "44b6"
    assert assignment["directions"]["6bba"]["movie_count"] == 59
    assert len(chunks) == 4 and [len(group) for group in chunks] == [15, 15, 15, 14]
    names = [name for group in chunks for name in group]
    assert len(names) == len(set(names)) == 59
    assert all(name.startswith("44b6_") and len(name) == 13 for name in names)
    assert config["target_ids"] == names
    for key in ("source_training", "source_handoff", "source_score", "source_graph_plan"):
        pinned(config[key], config[key + "_sha256"])
    training = json.loads(Path(config["source_training"]).read_text())
    handoff = json.loads(Path(config["source_handoff"]).read_text())
    source_score = json.loads(Path(config["source_score"]).read_text())
    source_plan = json.loads(Path(config["source_graph_plan"]).read_text())
    assert training["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    assert handoff["status"] == "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF"
    assert handoff["training_verified"]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert handoff["score_verified"]["source_score"] == source_score["source_score"] == 0.8458659187983504
    assert source_score["target_labels_read"] is False
    assert source_plan["experiment"] == "EXP236_SOURCE_GRAPH10"
    assert source_plan["checkpoint"] == config["checkpoint"]
    assert source_plan["checkpoint_sha256"] == CHECKPOINT_SHA
    assert source_plan["code"] == config["parent_graph_code"]
    assert source_plan["training_chain"][-1]["checkpoint_sha256"] == CHECKPOINT_SHA
    _manifest(Path(config["parent_graph_code"]), config["parent_graph_manifest_sha256"])
    assert "run_exp236_source_graph10_v2.py" in json.loads(
        (Path(config["parent_graph_code"]) / "code_manifest.json").read_text())
    pinned(config["coordinator"], config["coordinator_sha256"])
    coordinator = json.loads(Path(config["coordinator"]).read_text())
    assert coordinator["state_sha256"] == state_digest(coordinator)
    assert coordinator["status"] == "PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED"
    assert coordinator["movie_count"] == coordinator["graph_count"] == 59
    assert coordinator["all_leases_released"] is True
    assert coordinator["target_labels_read"] is False and coordinator["target_score_computed"] is False
    assert coordinator["frozen"]["assignment_sha256"] == ASSIGNMENT_SHA
    assert coordinator["frozen"]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert coordinator["frozen"]["prereg_sha256"] == config["prereg_sha256"]
    for key in ("source_training", "source_handoff", "source_score", "source_graph_plan"):
        assert coordinator["frozen"][key + "_sha256"] == config[key + "_sha256"]
    assert coordinator["frozen"]["chunks"] == chunks
    assert len(coordinator["chunks"]) == 4
    pinned(config["cohort"], COHORT_SHA)
    cohort_rows = json.loads(Path(config["cohort"]).read_text())["rows"]
    cohort = {row["dataset"]: row for row in cohort_rows}
    assert len(cohort_rows) == len(cohort) == 175
    assert {name for name in cohort if name.startswith("44b6_")} == set(names)
    pinned(config["evaluator_config"], config["evaluator_config_sha256"])
    queue_state = live_queue() if queue_state is None else queue_state
    requests = queue_state["requests"]
    assert isinstance(requests, list)
    candidate, graph_hashes, release_rows = {}, [], []
    for index, movies in enumerate(chunks):
        token = f"exp236_target44b6_chunk{index:02d}_v1_20260927"
        code = Path(REMOTE) / "code" / token
        run = Path(REMOTE) / "runs" / token
        entry = coordinator["chunks"][index]
        assert entry["stage"]["validated"] is True
        assert entry["launch"]["validated"] is True
        assert entry["postrun"]["validated"] is True
        assert len(entry["postrun"]["process_probe_sha256"]) == 64
        stage = entry["stage"]["result"]
        post = entry["postrun"]["gate"]
        assert stage["code"] == str(code) and stage["run"] == str(run)
        assert stage["movies"] == movies and stage["checkpoint_sha256"] == CHECKPOINT_SHA
        assert stage["source_handoff_sha256"] == config["source_handoff_sha256"]
        assert stage["lease_id"] == f"exp236-target44b6-chunk{index:02d}-v1-20260927"
        assert post["status"] == "PASS_EXP236_TARGET44B6_CHUNK_POSTRUN_NO_LABELS"
        assert post["chunk_index"] == index and post["movies"] == movies
        assert post["target_labels_read"] is False and post["queue_state_in_control"] == "RELEASED"
        for key in ("manifest_sha256", "plan_sha256", "checkpoint_sha256"):
            assert post[key] == stage[key]
        assert [row["dataset"] for row in post["graph_hashes"]] == movies
        _manifest(code, stage["manifest_sha256"])
        plan_path = code / "plan.json"
        pinned(plan_path, stage["plan_sha256"])
        plan = json.loads(plan_path.read_text())
        assert plan["experiment"] == "EXP236_TARGET44B6_CHUNK"
        assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
        assert plan["chunk_index"] == index and plan["chunk_count"] == 4
        assert plan["movies"] == movies and plan["assignment_sha256"] == ASSIGNMENT_SHA
        for key in ("source_training", "source_handoff", "source_score", "source_graph_plan"):
            assert plan[key + "_sha256"] == config[key + "_sha256"]
            assert sha(plan[key]) == config[key + "_sha256"]
        assert plan["checkpoint_sha256"] == CHECKPOINT_SHA and plan["checkpoint_epoch"] == 10
        assert plan["checkpoint"] == config["checkpoint"]
        assert plan["data_root"] == REMOTE + "/data/exp213_source_view_20260912"
        assert sha(plan["assignment"]) == ASSIGNMENT_SHA
        assert Path(plan["code"]).resolve() == code.resolve()
        assert Path(plan["output"]).resolve() == (run / "output").resolve()
        for filename, key in (("exit.json", "exit_sha256"),
                              ("supervision/complete.json", "supervision_sha256"),
                              ("supervision/control.json", "control_sha256"),
                              ("output/status.json", "status_sha256")):
            pinned(run / filename, post[key])
        exit_record = json.loads((run / "exit.json").read_text())
        supervision = json.loads((run / "supervision/complete.json").read_text())
        control = json.loads((run / "supervision/control.json").read_text())
        assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
        assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT" and supervision["exit"] == exit_record
        assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
        assert control["queue"]["id"] == stage["lease_id"]
        assert control["queue"]["run_path"] == str(run)
        live = [row for row in requests if row["id"] == stage["lease_id"]]
        assert len(live) == 1 and live[0]["state"] == "RELEASED" and live[0]["run_path"] == str(run)
        assert live[0]["owner"] == "biohub-agent"
        assert live[0]["gpus"] == [] and live[0]["process"] == entry["postrun"]["queue_row"]["process"]
        assert live[0]["process"]["pid"] == exit_record["pid"]
        assert live[0]["process"]["start"] == exit_record["start"]
        assert live_group_dead(live[0]["process"]["pid"])
        release_rows.append({"chunk_index": index, "lease_id": stage["lease_id"], "run": str(run),
                             "state": live[0]["state"]})
        status = json.loads((run / "output/status.json").read_text())
        assert status["status"] == f"PASS_EXP236_TARGET44B6_CHUNK{index:02d}_NO_LABELS"
        assert status["target_labels_read"] is False and status["movies"] == movies
        assert status["chunk_index"] == index and status["assignment_sha256"] == ASSIGNMENT_SHA
        assert status["source_handoff_sha256"] == config["source_handoff_sha256"]
        assert status["checkpoint_sha256"] == CHECKPOINT_SHA
        assert status["plan_sha256"] == stage["plan_sha256"]
        assert len(status["records"]) == len(movies)
        output = run / "output"
        expected = {"status.json"} | {"graph__" + name + suffix for name in movies
                                      for suffix in (".csv", ".json")}
        assert {path.name for path in output.iterdir()} == expected
        for name, record, graph_hash in zip(movies, status["records"], post["graph_hashes"]):
            csv_path = output / ("graph__" + name + ".csv")
            rec_path = csv_path.with_suffix(".json")
            shape = json.loads((Path(plan["data_root"]) / (name + ".zarr/0/zarr.json")).read_text())["shape"]
            assert record["dataset"] == name and record["shape"] == shape == cohort[name]["shape"]
            assert record["csv"] == str(csv_path)
            assert record["checkpoint_sha256"] == CHECKPOINT_SHA
            assert record["plan_sha256"] == stage["plan_sha256"]
            assert json.loads(rec_path.read_text()) == record
            pinned(csv_path, record["csv_sha256"])
            assert graph_hash == {"dataset": name, "csv_sha256": record["csv_sha256"],
                                  "receipt_sha256": sha(rec_path)}
            candidate[name] = checked_graph(csv_path, name, shape, record["nodes"], record["edges"])
            graph_hashes.append({"dataset": name, "csv_sha256": record["csv_sha256"],
                                 "receipt_sha256": graph_hash["receipt_sha256"]})
    assert len(candidate) == 59 and list(candidate) == names
    assert sum(len(chunk["postrun"]["gate"]["graph_hashes"])
               for chunk in coordinator["chunks"]) == 59
    pinned(config["checkpoint"], CHECKPOINT_SHA)
    old, baseline_rows, baseline, baseline_hashes = _baseline(config, cohort)
    runtime, contract = current_import_gate(config)
    images = image_metadata(config, cohort, names)
    gate_receipt = {"status": "PASS_EXP236_ALL_59_GRAPHS_BEFORE_LABEL_ACCESS",
                    "candidate_count": 59, "baseline_count": 59,
                    "assignment_sha256": ASSIGNMENT_SHA,
                    "source_handoff_sha256": config["source_handoff_sha256"],
                    "source_graph_plan_sha256": config["source_graph_plan_sha256"],
                    "checkpoint_sha256": CHECKPOINT_SHA,
                    "coordinator_sha256": config["coordinator_sha256"],
                    "cohort_sha256": COHORT_SHA,
                    "evaluator_config_sha256": config["evaluator_config_sha256"],
                    "current_metrics_sha256": CURRENT_METRICS_SHA,
                    "current_division_sha256": CURRENT_DIVISION_SHA,
                    "tracksdata_commit": TRACKSDATA_COMMIT,
                    "runtime": runtime, "synthetic_contract": contract,
                    "image_metadata": images, "image_scale_audit_sha256": IMAGE_AUDIT_SHA,
                    "baseline_target_rows_sha256": config["baseline_target_rows_sha256"],
                    "graph_hashes": graph_hashes, "live_release": release_rows,
                    "baseline_hashes": baseline_hashes, "target_labels_read": False}
    return cohort, candidate, old, baseline_rows, baseline, gate_receipt


def score_with_labels(config, cohort, candidate, old, baseline_rows, baseline, images):
    """Only called after the no_metric_gate file is durably written."""
    evaluator_pins(json.loads(Path(config["evaluator_config"]).read_text()))
    repo = Path(config["repo"])
    sys.path.insert(0, str(repo / "src"))
    from geff import GeffMetadata
    from biohub_tracking.metrics import evaluate as legacy_evaluate
    from biohub_tracking.metrics import node_recall as legacy_node_recall
    from biohub_tracking.metrics import per_sample_metrics as legacy_per_sample_metrics
    from biohub_tracking.metrics import summarise as legacy_summarise
    import polars as pl
    import tracksdata as td
    from types import SimpleNamespace
    from current_official.metrics import evaluate, node_recall, per_sample_metrics, summarise

    def build_graph(points, edges):
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

    def evaluate_current(graph, gt, *, scale):
        return evaluate(graph, gt, scale=scale, max_distance=7.0)

    scales = {row["dataset"]: tuple(row["scale"]) for row in images}
    legacy_rows, old_rows, new_rows = [], [], []
    for name in sorted(config["target_ids"]):
        label_path = Path(cohort[name]["zarr"]).with_suffix(".geff")
        loaded = td.graph.IndexedRXGraph.from_geff(label_path)
        gt = loaded[0] if isinstance(loaded, tuple) else loaded
        estimate = (GeffMetadata.read(label_path).extra or {}).get(
            "estimated_number_of_nodes")
        assert estimate is not None and math.isfinite(float(estimate)) and float(estimate) > 0
        dataset = SimpleNamespace(tracks=gt, scale=scales[name])
        legacy_row = score_one(name, old[name], dataset, estimate, legacy_evaluate,
                               legacy_node_recall, legacy_per_sample_metrics, build_graph)
        rows_close(legacy_row, baseline_rows[name], tol=1e-12)
        legacy_rows.append(legacy_row)
        old_rows.append(score_one(name, old[name], dataset, estimate, evaluate_current,
                                  node_recall, per_sample_metrics, build_graph))
        new_rows.append(score_one(name, candidate[name], dataset, estimate, evaluate_current,
                                  node_recall, per_sample_metrics, build_graph))
        assert old_rows[-1]["num_pred_nodes"] == baseline_rows[name]["num_pred_nodes"]
        assert new_rows[-1]["num_pred_nodes"] == len(candidate[name]["nodes"])
        print(json.dumps({"scored_movie": name}), flush=True)
    legacy_summary = legacy_summarise(legacy_rows)
    old_summary = summarise(old_rows)
    new_summary = summarise(new_rows)
    assert math.isfinite(old_summary["score"]) and math.isfinite(new_summary["score"])
    assert old_summary["n"] == new_summary["n"] == 59
    return legacy_rows, old_rows, new_rows, legacy_summary, old_summary, new_summary


def run(config, config_sha, *, queue_state=None, gate_only=False):
    pinned(config, config_sha)
    config = json.loads(Path(config).read_text())
    cohort, candidate, old, baseline_rows, baseline, gate_receipt = gate(config, queue_state)
    if gate_only:
        return gate_receipt
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    gate_path = output / "no_metric_gate.json"
    with gate_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(gate_receipt, indent=2) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    labels_before = label_manifest(cohort, config["target_ids"])
    label_path = output / "label_tree_hashes.json"
    with label_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(labels_before, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    legacy_rows, old_rows, new_rows, legacy_summary, old_summary, new_summary = score_with_labels(
        config, cohort, candidate, old, baseline_rows, baseline, gate_receipt["image_metadata"])
    assert label_manifest(cohort, config["target_ids"]) == labels_before
    result = {"status": "PASS_EXP236_SOURCE6BBA_TARGET44B6_CURRENT59",
              "evidence_class": config["evidence_class"],
              "no_metric_gate_sha256": sha(gate_path), "baseline_replay": "PASS_1e-12",
              "label_tree_hashes_sha256": sha(label_path),
              "metric_source": "current organizer commit 075fc5f5a52d11077f9dc2b074644618f26939e2",
              "current_metrics_sha256": CURRENT_METRICS_SHA,
              "current_division_sha256": CURRENT_DIVISION_SHA,
              "legacy_exp214_baseline_summary": legacy_summary,
              "baseline_summary": old_summary, "candidate_summary": new_summary,
              "delta_vs_current_baseline": new_summary["score"] - old_summary["score"],
              "legacy_exp214_baseline_rows": legacy_rows,
              "baseline_rows": old_rows, "candidate_rows": new_rows,
              "target_labels_read_after_graph_gate": True}
    with (output / "result.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--gate-only", action="store_true")
    args = parser.parse_args()
    result = run(args.config, args.config_sha256, gate_only=args.gate_only)
    print(json.dumps({"status": result["status"],
                      "score": result.get("candidate_summary", {}).get("score")}))


if __name__ == "__main__":
    main()
