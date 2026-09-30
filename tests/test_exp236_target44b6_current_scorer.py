"""Synthetic full 59-graph gate and label ordering for the EXP236 scorer."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import score_exp236_target44b6_current as scorer
from prepare_exp236_target44b6_scorer_local import verify_bundle
import stage_exp236_target44b6_scorer as stager
import launch_exp236_target44b6_scorer as launcher
import verify_exp236_target44b6_scorer as verifier


HEADER = "id,dataset,row_type,node_id,t,z,y,x,source_id,target_id\n"


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")
    return scorer.sha(path)


def csv(path, names):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [HEADER]
    for i, name in enumerate(names):
        j = i * 3
        rows += [f"{j},{name},node,1,0,0,0,0,-1,-1\n",
                 f"{j+1},{name},node,2,1,0,0,0,-1,-1\n",
                 f"{j+2},{name},edge,-1,-1,-1,-1,-1,1,2\n"]
    path.write_text("".join(rows))
    return scorer.sha(path)


def fixture(tmp_path, monkeypatch):
    root = tmp_path / "remote"
    monkeypatch.setattr(scorer, "REMOTE", str(root))
    monkeypatch.setattr(scorer, "live_group_dead", lambda _: True)
    monkeypatch.setattr(scorer, "current_import_gate", lambda _: ({"profile": "fake"},
                         {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"}))
    target = [f"44b6_{i:08x}" for i in range(59)]
    source = [f"6bba_{i:08x}" for i in range(116)]
    cohort_names = target + source
    chunks = [target[0:15], target[15:30], target[30:45], target[45:59]]
    assignment = {"status": "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS",
                  "target_labels_read": False, "thresholds_selected": False,
                  "directions": {"6bba": {"target_embryo": "44b6", "movie_count": 59,
                                            "chunks": chunks}}}
    assignment_path = tmp_path / "assignment.json"
    assignment_sha = put(assignment_path, assignment)
    monkeypatch.setattr(scorer, "ASSIGNMENT_SHA", assignment_sha)
    checkpoint = tmp_path / "last.pt"
    checkpoint.write_text("epoch10")
    checkpoint_sha = scorer.sha(checkpoint)
    monkeypatch.setattr(scorer, "CHECKPOINT_SHA", checkpoint_sha)
    documents = {}
    for key, value in {
        "source_training": {"status": "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"},
        "source_handoff": {"status": "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF",
                           "training_verified": {"checkpoint_sha256": checkpoint_sha},
                           "score_verified": {"source_score": 0.8458659187983504}},
        "source_score": {"source_score": 0.8458659187983504, "target_labels_read": False},
        "source_graph_plan": {"experiment": "EXP236_SOURCE_GRAPH10",
                              "checkpoint": str(checkpoint), "checkpoint_sha256": checkpoint_sha,
                              "code": str(root / "code/parent"),
                              "training_chain": [{"checkpoint_sha256": checkpoint_sha}]},
    }.items():
        path = tmp_path / (key + ".json")
        documents[key] = (path, put(path, value))
    parent = root / "code/parent"
    wrapper_sha = put(parent / "run_exp236_source_graph10_v2.py", {"fake": True})
    parent_manifest_sha = put(parent / "code_manifest.json",
                              {"run_exp236_source_graph10_v2.py": wrapper_sha})
    monkeypatch.setattr(scorer, "PARENT_MANIFEST_SHA", parent_manifest_sha)
    for key, constant in (("source_training", "TRAINING_SHA"),
                          ("source_handoff", "HANDOFF_SHA"),
                          ("source_score", "SOURCE_SCORE_SHA"),
                          ("source_graph_plan", "SOURCE_PLAN_SHA")):
        monkeypatch.setattr(scorer, constant, documents[key][1])
    monkeypatch.setattr(scorer, "PREREG_SHA", "p" * 64)
    data_root_text = scorer.REMOTE + "/data/exp213_source_view_20260912"
    data_root = Path(data_root_text)
    cohort_rows, image_rows = [], []
    for name in cohort_names:
        zarr = data_root / (name + ".zarr")
        root_sha = put(zarr / "zarr.json", {"attributes": {"multiscales": [{"datasets": [
            {"coordinateTransformations": [{"type": "scale", "scale":
                                            [1, 1.625, 0.40625, 0.40625]}]}]}]}})
        array_sha = put(zarr / "0/zarr.json", {"shape": [2, 1, 1, 1]})
        cohort_rows.append({"dataset": name, "shape": [2, 1, 1, 1], "zarr": str(zarr)})
        image_rows.append({"dataset": name, "zarr_root_sha256": root_sha,
                           "zarr_array_sha256": array_sha,
                           "scale": [1.625, 0.40625, 0.40625]})
    cohort_path = tmp_path / "cohort.json"
    cohort_sha = put(cohort_path, {"rows": cohort_rows})
    monkeypatch.setattr(scorer, "COHORT_SHA", cohort_sha)
    image_audit = tmp_path / "image_scale_audit.json"
    audit_sha = put(image_audit,
                    {"status": "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS",
                     "rows": image_rows})
    monkeypatch.setattr(scorer, "IMAGE_AUDIT_SHA", audit_sha)
    baseline_parts = []
    groups = [target[0:12], target[12:24], target[24:36], target[36:48], target[48:59],
              source[0:40], source[40:80], source[80:116]]
    for i, names in enumerate(groups):
        marker = "44b6" if i < 5 else "6bba"
        path = tmp_path / f"baseline_{marker}_{i}" / "submission.csv"
        csv_sha = csv(path, names)
        receipt_sha = put(path.parent / "inference_receipt.json",
                          {"submission_sha256": csv_sha, "movies": names})
        baseline_parts.append({"csv": str(path), "sha256": csv_sha,
                               "receipt_sha256": receipt_sha})
    baseline_rows = [{"dataset": n, "score": 0.5} for n in cohort_names]
    baseline = {"status": "PASS_HONEST_PAIRED_CV",
                "summary": {"public": {"score": 0.7427291486246141}},
                "rows": {"public": baseline_rows},
                "input_hashes": {"public": baseline_parts}}
    baseline_path = tmp_path / "baseline.json"
    baseline_sha = put(baseline_path, baseline)
    monkeypatch.setattr(scorer, "BASELINE_SHA", baseline_sha)
    target_rows_sha = hashlib.sha256(json.dumps(baseline_rows[:59], sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    evaluator = tmp_path / "evaluator.json"
    evaluator_sha = put(evaluator, {})
    metric = tmp_path / "current_official/metrics.py"
    division = tmp_path / "current_official/division_metrics.py"
    metric.parent.mkdir()
    metric.write_text("# metric\n")
    division.write_text("# division\n")
    monkeypatch.setattr(scorer, "CURRENT_METRICS_SHA", scorer.sha(metric))
    monkeypatch.setattr(scorer, "CURRENT_DIVISION_SHA", scorer.sha(division))
    queue_rows, coord_chunks = [], []
    for i, names in enumerate(chunks):
        token = f"exp236_target44b6_chunk{i:02d}_v1_20260927"
        code, run = root / "code" / token, root / "runs" / token
        lease = f"exp236-target44b6-chunk{i:02d}-v1-20260927"
        process = {"pid": 10000 + i, "start": str(i)}
        queue_rows.append({"id": lease, "state": "RELEASED", "run_path": str(run),
                           "owner": "biohub-agent", "gpus": [], "process": process})
        plan = {"experiment": "EXP236_TARGET44B6_CHUNK", "source_embryo": "6bba",
                "target_embryo": "44b6", "chunk_index": i, "chunk_count": 4,
                "movies": names, "assignment_sha256": assignment_sha,
                "assignment": str(assignment_path), "checkpoint_sha256": checkpoint_sha,
                "checkpoint_epoch": 10, "checkpoint": str(checkpoint),
                "code": str(code), "output": str(run / "output"),
                "data_root": data_root_text}
        for key, (path, digest) in documents.items():
            plan[key] = str(path)
            plan[key + "_sha256"] = digest
        plan_sha = put(code / "plan.json", plan)
        manifest_sha = put(code / "code_manifest.json", {"plan.json": plan_sha})
        exit_record = {"returncode": 0, "hard_timeout": False, **process}
        exit_sha = put(run / "exit.json", exit_record)
        completion_sha = put(run / "supervision/complete.json",
                             {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record})
        control_sha = put(run / "supervision/control.json",
                          {"action": "release", "queue": {"id": lease, "state": "RELEASED",
                                                             "run_path": str(run)}})
        records, hashes = [], []
        for name in names:
            path = run / "output" / ("graph__" + name + ".csv")
            csv_sha = csv(path, [name])
            rec = {"dataset": name, "shape": [2, 1, 1, 1], "csv": str(path),
                   "csv_sha256": csv_sha, "checkpoint_sha256": checkpoint_sha,
                   "plan_sha256": plan_sha, "nodes": 2, "edges": 1}
            rec_sha = put(path.with_suffix(".json"), rec)
            records.append(rec)
            hashes.append({"dataset": name, "csv_sha256": csv_sha,
                           "receipt_sha256": rec_sha})
        status_sha = put(run / "output/status.json",
                         {"status": f"PASS_EXP236_TARGET44B6_CHUNK{i:02d}_NO_LABELS",
                          "target_labels_read": False, "movies": names, "chunk_index": i,
                          "assignment_sha256": assignment_sha,
                          "source_handoff_sha256": documents["source_handoff"][1],
                          "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
                          "records": records})
        stage = {"code": str(code), "run": str(run), "movies": names,
                 "checkpoint_sha256": checkpoint_sha,
                 "source_handoff_sha256": documents["source_handoff"][1],
                 "lease_id": lease, "manifest_sha256": manifest_sha, "plan_sha256": plan_sha}
        post = {"status": "PASS_EXP236_TARGET44B6_CHUNK_POSTRUN_NO_LABELS",
                "chunk_index": i, "movies": names, "target_labels_read": False,
                "queue_state_in_control": "RELEASED", "manifest_sha256": manifest_sha,
                "plan_sha256": plan_sha, "checkpoint_sha256": checkpoint_sha,
                "status_sha256": status_sha, "exit_sha256": exit_sha,
                "supervision_sha256": completion_sha, "control_sha256": control_sha,
                "graph_hashes": hashes}
        coord_chunks.append({"stage": {"validated": True, "result": stage},
                             "launch": {"validated": True, "result": {"lease": {}}},
                             "postrun": {"validated": True, "gate": post,
                                         "process_probe_sha256": "a" * 64,
                                         "queue_row": queue_rows[-1]}})
    frozen = {"assignment_sha256": assignment_sha, "prereg_sha256": "p" * 64,
              "checkpoint_sha256": checkpoint_sha, "chunks": chunks}
    for key, (_, digest) in documents.items():
        frozen[key + "_sha256"] = digest
    coordinator = {"status": "PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED",
                   "movie_count": 59, "graph_count": 59, "all_leases_released": True,
                   "target_labels_read": False, "target_score_computed": False,
                   "frozen": frozen, "chunks": coord_chunks}
    coordinator["state_sha256"] = scorer.state_digest(coordinator)
    coordinator_path = tmp_path / "coordinator.json"
    coordinator_sha = put(coordinator_path, coordinator)
    config = {"experiment": "EXP236_SOURCE6BBA_TARGET44B6_CURRENT59",
              "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
              "assignment": str(assignment_path), "assignment_sha256": assignment_sha,
              "checkpoint": str(checkpoint), "checkpoint_sha256": checkpoint_sha,
              "prereg_sha256": frozen["prereg_sha256"],
              "parent_graph_code": str(parent),
              "parent_graph_manifest_sha256": parent_manifest_sha,
              "coordinator": str(coordinator_path), "coordinator_sha256": coordinator_sha,
              "target_ids": target, "cohort": str(cohort_path), "cohort_sha256": cohort_sha,
              "baseline_metrics": str(baseline_path), "baseline_metrics_sha256": baseline_sha,
              "baseline_input_hashes": baseline_parts,
              "baseline_target_rows_sha256": target_rows_sha,
              "evaluator_config": str(evaluator), "evaluator_config_sha256": evaluator_sha,
              "current_metrics": str(metric), "current_metrics_sha256": scorer.sha(metric),
              "current_division": str(division), "current_division_sha256": scorer.sha(division),
              "tracksdata_commit": scorer.TRACKSDATA_COMMIT,
              "image_scale_audit": str(image_audit), "image_scale_audit_sha256": audit_sha,
              "python": sys.executable,
              "repo": str(tmp_path / "repo"), "data_dir": str(data_root),
              "output": str(tmp_path / "score_output")}
    for key, (path, digest) in documents.items():
        config[key] = str(path)
        config[key + "_sha256"] = digest
    config_path = tmp_path / "score_config.json"
    config_sha = put(config_path, config)
    return config, config_path, config_sha, {"requests": queue_rows}, root


def test_full_gate_then_durable_label_order(tmp_path, monkeypatch):
    config, path, digest, queue, _ = fixture(tmp_path, monkeypatch)
    gate = scorer.run(path, digest, queue_state=queue, gate_only=True)
    assert gate["status"] == "PASS_EXP236_ALL_59_GRAPHS_BEFORE_LABEL_ACCESS"
    assert gate["candidate_count"] == gate["baseline_count"] == 59
    assert not Path(config["output"]).exists()
    monkeypatch.setattr(scorer, "label_manifest", lambda *_: {"fake": "hash"})

    def labels(cfg, *_):
        assert json.loads((Path(cfg["output"]) / "no_metric_gate.json").read_text())[
            "target_labels_read"] is False
        return [], [], [], {"score": 0.4}, {"score": 0.5}, {"score": 0.6}

    monkeypatch.setattr(scorer, "score_with_labels", labels)
    result = scorer.run(path, digest, queue_state=queue)
    assert result["status"] == "PASS_EXP236_SOURCE6BBA_TARGET44B6_CURRENT59"
    assert result["delta_vs_current_baseline"] == pytest.approx(0.1)
    with pytest.raises(FileExistsError):
        scorer.run(path, digest, queue_state=queue)


@pytest.mark.parametrize("damage", ["running_lease", "csv_tamper", "baseline_tamper",
                                      "incomplete_coordinator", "wrong_metric_hash"])
def test_tamper_blocks_before_labels(tmp_path, monkeypatch, damage):
    config, path, digest, queue, root = fixture(tmp_path, monkeypatch)
    if damage == "running_lease":
        queue["requests"][0]["state"] = "RUNNING"
    elif damage == "csv_tamper":
        target = root / "runs/exp236_target44b6_chunk00_v1_20260927/output/graph__44b6_00000000.csv"
        target.write_text(target.read_text() + "junk\n")
    elif damage == "baseline_tamper":
        with Path(config["baseline_metrics"]).open("a") as stream:
            stream.write(" ")
    elif damage == "incomplete_coordinator":
        coordinator = Path(config["coordinator"])
        state = json.loads(coordinator.read_text())
        state["status"] = "ACTIVE_NO_TARGET_LABELS"
        state["state_sha256"] = scorer.state_digest(state)
        put(coordinator, state)
        config["coordinator_sha256"] = scorer.sha(coordinator)
        digest = put(path, config)
    else:
        config["current_metrics_sha256"] = "0" * 64
        digest = put(path, config)
    monkeypatch.setattr(scorer, "score_with_labels",
                        lambda *_: pytest.fail("labels opened before all guards"))
    with pytest.raises((AssertionError, ValueError)):
        scorer.run(path, digest, queue_state=queue)
    assert not Path(config["output"]).exists()


def test_bundle_and_future_source_are_local_only():
    source = launcher.source({"stage": {"manifest_sha256": "a" * 64,
                                       "score_config_sha256": "b" * 64}})
    compile(source, "remote_cpu_launch.py", "exec")
    probe = verifier.remote_probe({"stage": {"manifest_sha256": "a" * 64,
                                             "score_config_sha256": "b" * 64},
                                  "config": {"output": verifier.RUN + "/output"}},
                                 {"wrapper_pid": 123})
    compile(probe, "remote_verify.py", "exec")
    assert "59" in probe and "EXP236" in source
