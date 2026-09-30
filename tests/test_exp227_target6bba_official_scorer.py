"""Synthetic end-to-end no-label gate and label-order controls for EXP227."""
import hashlib
import ast
import json
from pathlib import Path
import sys
import types

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import score_exp227_target6bba_official as scorer
from score_exp223_official import rows_close
import launch_exp227_target6bba_scorer as launcher
import stage_exp227_target6bba_scorer as stager
import verify_exp227_target6bba_scorer as verifier
from prepare_exp227_target6bba_scorer_local import verify_bundle


HEADER = "id,dataset,row_type,node_id,t,z,y,x,source_id,target_id\n"


def write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return scorer.sha(path)


def put(path, value):
    return write(path, json.dumps(value, indent=2) + "\n")


def csv_rows(names):
    rows, idx = [HEADER], 0
    for name in names:
        rows.extend((f"{idx},{name},node,1,0,0,0,0,-1,-1\n",
                     f"{idx+1},{name},node,2,1,0,0,0,-1,-1\n",
                     f"{idx+2},{name},edge,-1,-1,-1,-1,-1,1,2\n"))
        idx += 3
    return "".join(rows)


def fixture(tmp_path, monkeypatch):
    root = tmp_path / "remote"
    monkeypatch.setattr(scorer, "REMOTE", str(root))
    target = [f"6bba_{i:08x}" for i in range(116)]
    chunks = [target[i * 15:(i + 1) * 15] for i in range(4)]
    chunks += [target[60 + i * 14:60 + (i + 1) * 14] for i in range(4)]
    assignment = {"status": "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS",
                  "target_labels_read": False, "thresholds_selected": False,
                  "directions": {"44b6": {"target_embryo": "6bba", "movie_count": 116,
                                             "chunks": chunks}}}
    assignment_path = tmp_path / "assignment.json"
    assignment_sha = put(assignment_path, assignment)
    monkeypatch.setattr(scorer, "ASSIGNMENT_SHA", assignment_sha)
    checkpoint = tmp_path / "epoch_010.pt"
    checkpoint_sha = write(checkpoint, "frozen checkpoint")
    monkeypatch.setattr(scorer, "CHECKPOINT_SHA", checkpoint_sha)
    selection = {"status": "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT", "selected_epoch": 10,
                 "target_labels_read": False, "checkpoint": str(checkpoint),
                 "checkpoint_sha256": checkpoint_sha, "prereg_sha256": "prereg",
                 "scores": {"10": 0.8114, "20": 0.8068}}
    selection_path = tmp_path / "selection.json"
    selection_sha = put(selection_path, selection)
    source = [f"44b6_{i:08x}" for i in range(59)]
    cohort_names = source + target
    data_root_text = scorer.REMOTE + "/data/exp213_source_view_20260912"
    data_root = Path(data_root_text)
    cohort_rows = []
    for name in cohort_names:
        zarr = data_root / (name + ".zarr")
        if name in target:
            put(zarr / "0/zarr.json", {"shape": [2, 1, 1, 1]})
        cohort_rows.append({"dataset": name, "shape": [2, 1, 1, 1], "zarr": str(zarr)})
    cohort_path = tmp_path / "cohort.json"
    cohort_sha = put(cohort_path, {"rows": cohort_rows})
    monkeypatch.setattr(scorer, "COHORT_SHA", cohort_sha)
    baseline_parts = []
    for index in range(8):
        names = cohort_names[index * 22:(index + 1) * 22] if index < 7 else cohort_names[154:]
        output = tmp_path / f"baseline{index}" / "output"
        csv_path = output / "submission.csv"
        csv_sha = write(csv_path, csv_rows(names))
        receipt_sha = put(output / "inference_receipt.json",
                          {"submission_sha256": csv_sha, "movies": names})
        baseline_parts.append({"csv": str(csv_path), "sha256": csv_sha,
                               "receipt_sha256": receipt_sha})
    baseline = {"status": "PASS_HONEST_PAIRED_CV",
                "summary": {"public": {"score": 0.7427291486246141}},
                "rows": {"public": [{"dataset": name, "score": 0.5} for name in cohort_names]},
                "input_hashes": {"public": baseline_parts}}
    baseline_path = tmp_path / "baseline.json"
    baseline_sha = put(baseline_path, baseline)
    monkeypatch.setattr(scorer, "BASELINE_SHA", baseline_sha)
    evaluator_path = tmp_path / "evaluator.json"
    evaluator_sha = write(evaluator_path, "{}\n")
    current_metrics = tmp_path / "current_official/metrics.py"
    current_division = tmp_path / "current_official/division_metrics.py"
    current_metrics_sha = write(current_metrics, "# synthetic current metric\n")
    current_division_sha = write(current_division, "# synthetic division metric\n")
    monkeypatch.setattr(scorer, "CURRENT_METRICS_SHA", current_metrics_sha)
    monkeypatch.setattr(scorer, "CURRENT_DIVISION_SHA", current_division_sha)
    monkeypatch.setattr(scorer, "current_import_gate", lambda _: None)
    queue_rows, coord_chunks = [], []
    for index, names in enumerate(chunks):
        token = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
        code, run = root / "code" / token, root / "runs" / token
        lease = f"exp227-target6bba-chunk{index:02d}-v1-20260927"
        queue_rows.append({"id": lease, "state": "RELEASED", "run_path": str(run),
                           "owner": "biohub-agent"})
        plan = {"experiment": "EXP227_TARGET6BBA_CHUNK", "source_embryo": "44b6",
                "target_embryo": "6bba", "chunk_index": index, "chunk_count": 8,
                "movies": names, "assignment_sha256": assignment_sha,
                "selection_sha256": selection_sha, "checkpoint_sha256": checkpoint_sha,
                "checkpoint_epoch": 10, "checkpoint": str(checkpoint),
                "assignment": str(assignment_path), "selection": str(selection_path),
                "code": str(code), "output": str(run / "output"), "data_root": data_root_text}
        plan_sha = put(code / "plan.json", plan)
        manifest_sha = put(code / "code_manifest.json", {"plan.json": plan_sha})
        exit_record = {"returncode": 0, "hard_timeout": False}
        exit_sha = put(run / "exit.json", exit_record)
        supervision_sha = put(run / "supervision/complete.json",
                              {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record})
        control_sha = put(run / "supervision/control.json",
                          {"action": "release", "queue": {"id": lease, "state": "RELEASED",
                                                           "run_path": str(run)}})
        records, graph_hashes = [], []
        for name in names:
            path = run / "output" / ("graph__" + name + ".csv")
            csv_sha = write(path, csv_rows([name]))
            record = {"dataset": name, "shape": [2, 1, 1, 1], "csv": str(path),
                      "csv_sha256": csv_sha, "checkpoint_sha256": checkpoint_sha,
                      "plan_sha256": plan_sha, "nodes": 2, "edges": 1}
            receipt_sha = put(path.with_suffix(".json"), record)
            records.append(record)
            graph_hashes.append({"dataset": name, "csv_sha256": csv_sha,
                                 "receipt_sha256": receipt_sha})
        status = {"status": f"PASS_EXP227_TARGET6BBA_CHUNK{index:02d}_NO_LABELS",
                  "target_labels_read": False, "movies": names, "chunk_index": index,
                  "assignment_sha256": assignment_sha, "selection_sha256": selection_sha,
                  "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
                  "records": records}
        status_sha = put(run / "output/status.json", status)
        stage = {"code": str(code), "run": str(run), "movies": names,
                 "checkpoint_sha256": checkpoint_sha, "selection_sha256": selection_sha,
                 "lease_id": lease, "manifest_sha256": manifest_sha, "plan_sha256": plan_sha}
        post = {"status": "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS",
                "chunk_index": index, "movies": names, "target_labels_read": False,
                "queue_state_in_control": "RELEASED", "manifest_sha256": manifest_sha,
                "plan_sha256": plan_sha, "checkpoint_sha256": checkpoint_sha,
                "status_sha256": status_sha, "exit_sha256": exit_sha,
                "supervision_sha256": supervision_sha, "control_sha256": control_sha,
                "graph_hashes": graph_hashes}
        coord_chunks.append({"stage": {"validated": True, "result": stage},
                             "launch": {"validated": True},
                             "postrun": {"validated": True, "gate": post}})
    coordinator = {"status": "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED",
                   "movie_count": 116, "graph_count": 116, "all_leases_released": True,
                   "target_labels_read": False, "target_score_computed": False,
                   "frozen": {"assignment_sha256": assignment_sha,
                              "selection_sha256": selection_sha,
                              "checkpoint_sha256": checkpoint_sha,
                              "prereg_sha256": "prereg", "chunks": chunks},
                   "chunks": coord_chunks}
    coordinator["state_sha256"] = scorer.state_digest(coordinator)
    coordinator_path = tmp_path / "coordinator.json"
    coordinator_sha = put(coordinator_path, coordinator)
    config = {"experiment": "EXP227_SOURCE44_TARGET6BBA_OFFICIAL116",
              "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
              "assignment": str(assignment_path), "assignment_sha256": assignment_sha,
              "selection": str(selection_path), "selection_sha256": selection_sha,
              "checkpoint_sha256": checkpoint_sha,
              "coordinator": str(coordinator_path), "coordinator_sha256": coordinator_sha,
              "target_ids": target, "cohort": str(cohort_path), "cohort_sha256": cohort_sha,
              "baseline_metrics": str(baseline_path), "baseline_metrics_sha256": baseline_sha,
              "evaluator_config": str(evaluator_path), "evaluator_config_sha256": evaluator_sha,
              "current_metrics": str(current_metrics), "current_metrics_sha256": current_metrics_sha,
              "current_division": str(current_division), "current_division_sha256": current_division_sha,
              "repo": str(tmp_path / "repo"), "data_dir": str(data_root),
              "output": str(tmp_path / "score_output")}
    config_path = tmp_path / "score_config.json"
    config_sha = put(config_path, config)
    return config, config_path, config_sha, {"requests": queue_rows}, root


def test_full_116_gate_and_label_order(tmp_path, monkeypatch):
    config, path, digest, queue, _ = fixture(tmp_path, monkeypatch)
    _, candidate, old, baseline_rows, baseline, gate = scorer.gate(config, queue)
    assert len(candidate) == len(old) == 116
    assert len(baseline_rows) == 175 and baseline["status"] == "PASS_HONEST_PAIRED_CV"
    assert gate["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    calls = []

    def label_reader(cfg, *_):
        gate_path = Path(cfg["output"]) / "no_metric_gate.json"
        assert gate_path.is_file()
        assert json.loads(gate_path.read_text())["target_labels_read"] is False
        calls.append(1)
        return [], [], [], {"score": 0.4}, {"score": 0.5}, {"score": 0.6}

    monkeypatch.setattr(scorer, "score_with_labels", label_reader)
    result = scorer.run(path, digest, queue_state=queue)
    assert calls == [1] and result["no_metric_gate_sha256"] == scorer.sha(
        Path(config["output"]) / "no_metric_gate.json")
    assert result["evidence_class"].startswith("leakage-controlled")
    with pytest.raises(FileExistsError):
        scorer.run(path, digest, queue_state=queue)
    assert calls == [1]


@pytest.mark.parametrize("damage", ("running_lease", "csv_tamper", "extra_output", "baseline_tamper"))
def test_tamper_blocks_before_labels(tmp_path, monkeypatch, damage):
    config, path, digest, queue, root = fixture(tmp_path, monkeypatch)
    if damage == "running_lease":
        queue["requests"][3]["state"] = "RUNNING"
    elif damage == "csv_tamper":
        csv_path = next((root / "runs/exp227_target6bba_chunk00_v1_20260927/output").glob("*.csv"))
        csv_path.write_text(csv_path.read_text() + "junk\n")
    elif damage == "extra_output":
        write(root / "runs/exp227_target6bba_chunk00_v1_20260927/output/extra.csv", "extra")
    else:
        with Path(config["baseline_metrics"]).open("a") as stream:
            stream.write(" ")
    monkeypatch.setattr(scorer, "score_with_labels",
                        lambda *_: pytest.fail("target labels opened before gate"))
    with pytest.raises((AssertionError, ValueError)):
        scorer.run(path, digest, queue_state=queue)
    assert not Path(config["output"]).exists()


def test_exp214_exact_row_replay_rejects_change():
    row = {"dataset": "6bba_00000000", "score": 0.7427291486246141, "nodes": 3}
    rows_close(dict(row), row, tol=1e-12)
    with pytest.raises(SystemExit):
        rows_close({**row, "score": row["score"] + 1e-8}, row, tol=1e-12)


def test_scorer_replays_baseline_before_candidate_row(tmp_path, monkeypatch):
    name = "6bba_00000000"
    root = tmp_path / "repo"
    evaluator = tmp_path / "evaluator.json"
    evaluator.write_text("{}")
    config = {"target_ids": [name], "evaluator_config": str(evaluator), "repo": str(root),
              "data_dir": str(tmp_path), "output": str(tmp_path / "output")}
    fake_geff = types.ModuleType("geff")
    fake_geff.GeffMetadata = types.SimpleNamespace(read=lambda path: types.SimpleNamespace(
        extra={"estimated_number_of_nodes": 1}))
    package = types.ModuleType("biohub_tracking")
    package.__path__ = []
    io = types.ModuleType("biohub_tracking.io")
    io.open_dataset = lambda *_args, **_kwargs: object()
    metrics = types.ModuleType("biohub_tracking.metrics")
    metrics.evaluate = object()
    metrics.node_recall = object()
    metrics.per_sample_metrics = object()
    metrics.summarise = lambda rows: {"score": sum(row["score"] for row in rows) / len(rows)}
    predictor = types.ModuleType("predict_unet_transformer")
    predictor.build_graph = object()
    current_package = types.ModuleType("current_official")
    current_package.__path__ = []
    current_metrics = types.ModuleType("current_official.metrics")
    current_metrics.evaluate = object()
    current_metrics.node_recall = object()
    current_metrics.per_sample_metrics = object()
    current_metrics.summarise = metrics.summarise
    for key, module in {"geff": fake_geff, "biohub_tracking": package,
                        "biohub_tracking.io": io, "biohub_tracking.metrics": metrics,
                        "predict_unet_transformer": predictor,
                        "current_official": current_package,
                        "current_official.metrics": current_metrics}.items():
        monkeypatch.setitem(sys.modules, key, module)
    monkeypatch.setattr(scorer, "evaluator_pins", lambda _: None)
    calls = []

    def fake_score(dataset, graph, *_):
        calls.append(graph)
        return {"dataset": dataset, "score": 0.51 if graph == "old" else 0.6}

    monkeypatch.setattr(scorer, "score_one", fake_score)
    saved_path = list(sys.path)
    try:
        with pytest.raises(SystemExit):
            scorer.score_with_labels(config, {name: {"zarr": "synthetic"}}, {name: "new"},
                                     {name: "old"}, {name: {"dataset": name, "score": 0.5}}, {})
        assert calls == ["old"]
        monkeypatch.setattr(scorer, "score_one", lambda ds, graph, *_: {
            "dataset": ds, "score": 0.5 if graph == "old" else 0.6})
        _, _, _, legacy_summary, old_summary, new_summary = scorer.score_with_labels(
            config, {name: {"zarr": "synthetic"}}, {name: "new"}, {name: "old"},
            {name: {"dataset": name, "score": 0.5}}, {})
        assert legacy_summary["score"] == old_summary["score"] == 0.5
        assert new_summary["score"] == 0.6
    finally:
        sys.path[:] = saved_path


def test_local_bundle_and_generated_remote_code_parse():
    manifest_sha, manifest = verify_bundle()
    assert len(manifest_sha) == 64 and "score_exp227_target6bba_official.py" in manifest
    local = json.loads(stager.LOCAL.read_text())
    transmitted = stager.sealed_sources(local)
    assert stager.text_sha(transmitted["assignment.json"]) == scorer.ASSIGNMENT_SHA
    assert stager.text_sha(transmitted["selection.json"]) == manifest["selection.json"]
    assert "\r\n" in transmitted["assignment.json"]
    prepared = {"stage": {"manifest_sha256": "a" * 64,
                           "score_config_sha256": "b" * 64}, "config": {}}
    generated = launcher.source(prepared)
    tree = ast.parse(generated)
    wrapper_assignment = next(node for node in tree.body
                              if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name) and target.id == "wrapper"
                                      for target in node.targets))
    wrapper = ast.literal_eval(wrapper_assignment.value)
    ast.parse(wrapper.replace("__RUN__", repr("/tmp/run"))
              .replace("__CODE__", repr("/tmp/code"))
              .replace("__PYTHON__", repr("/tmp/python"))
              .replace("__CONFIG_SHA__", repr("b" * 64)))
    ast.parse(verifier.remote_probe(prepared, {"wrapper_pid": 123}))
    assert "assert not run.exists()" in generated
    assert "--config-sha256" in wrapper


def test_stage_and_launch_intents_are_one_shot(tmp_path, monkeypatch):
    stage_intent = tmp_path / "stage_intent.json"
    stage_intent.write_text("{}")
    monkeypatch.setattr(stager, "INTENT", stage_intent)
    monkeypatch.setattr(stager, "RECEIPT", tmp_path / "stage_receipt.json")
    monkeypatch.setattr(stager, "ssh", lambda *_: pytest.fail("remote stage attempted"))
    with pytest.raises(AssertionError):
        stager.stage()
    launch_intent = tmp_path / "launch_intent.json"
    launch_intent.write_text("{}")
    monkeypatch.setattr(launcher, "INTENT", launch_intent)
    monkeypatch.setattr(launcher, "RECEIPT", tmp_path / "launch_receipt.json")
    monkeypatch.setattr(launcher, "ssh", lambda *_: pytest.fail("remote launch attempted"))
    with pytest.raises(AssertionError):
        launcher.launch()
