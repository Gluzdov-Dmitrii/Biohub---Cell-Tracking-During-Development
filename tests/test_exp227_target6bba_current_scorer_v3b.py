"""Successor-bound EXP227 scorer and explicit fresh-coordinator stage gate."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import score_exp227_target6bba_current_v3 as v3
import score_exp227_target6bba_current_v3b as scorer
import stage_exp227_target6bba_scorer_v3b as stager
import launch_exp227_target6bba_scorer_v3b as launcher
import verify_exp227_target6bba_scorer_v3b as verifier
from test_exp227_target6bba_current_scorer_v3 import fixture as v3_fixture
from test_exp227_target6bba_official_scorer import put


def fixture(tmp_path, monkeypatch):
    config, path, _, queue, root = v3_fixture(tmp_path, monkeypatch)
    for key in ("REMOTE", "ASSIGNMENT_SHA", "CHECKPOINT_SHA", "COHORT_SHA",
                "BASELINE_SHA", "CURRENT_METRICS_SHA", "CURRENT_DIVISION_SHA"):
        monkeypatch.setattr(scorer, key, getattr(v3, key))
    monkeypatch.setattr(scorer, "current_import_gate", lambda _: ({"profile": "fake"},
                         {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"}))
    monkeypatch.setattr(scorer, "image_metadata", lambda _, __, names: [
        {"dataset": name, "scale": [1.625, 0.40625, 0.40625]} for name in names])
    coord = json.loads(Path(config["coordinator"]).read_text())
    final = coord["chunks"][7]["stage"]["result"]
    token = "exp227_target6bba_chunk07_v1_20260927"
    successor = {"status": "PREPARED_EXP227_CHUNK07_WAITSAFE_V2_LOCAL_ONLY",
                 "identity": {"token": token, "code": final["code"], "run": final["run"],
                              "lease_id": final["lease_id"]},
                 "plan_sha256": final["plan_sha256"]}
    successor_path = tmp_path / "successor_prepare.json"
    successor_sha = put(successor_path, successor)
    successor_stage = {"status": "STAGED_EXP227_CHUNK07_WAITSAFE_V2_NO_LABELS",
                       "code": final["code"], "run": final["run"],
                       "lease_id": final["lease_id"], "plan_sha256": final["plan_sha256"],
                       "manifest_sha256": final["manifest_sha256"],
                       "target_labels_read": False}
    stage_path = tmp_path / "successor_stage.json"
    stage_sha = put(stage_path, successor_stage)
    for key, value in (("SUCCESSOR_PREPARE_SHA", successor_sha),
                       ("SUCCESSOR_STAGE_SHA", stage_sha),
                       ("SUCCESSOR_MANIFEST_SHA", final["manifest_sha256"]),
                       ("SUCCESSOR_PLAN_SHA", final["plan_sha256"]),
                       ("SUCCESSOR_TOKEN", token),
                       ("SUCCESSOR_LEASE", final["lease_id"])):
        monkeypatch.setattr(scorer, key, value)
    config["experiment"] = "EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3B"
    config["successor_prepare"] = str(successor_path)
    config["successor_prepare_sha256"] = successor_sha
    config["successor_stage"] = str(stage_path)
    config["successor_stage_sha256"] = stage_sha
    hashes = [row for chunk in coord["chunks"]
              for row in chunk["postrun"]["gate"]["graph_hashes"]]
    config["final_graph_hashes_sha256"] = hashlib.sha256(json.dumps(hashes,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    digest = put(path, config)
    return config, path, digest, queue


def test_successor_binding_and_final_graph_hash_gate(tmp_path, monkeypatch):
    config, path, digest, queue = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(scorer, "label_manifest", lambda *_: pytest.fail("label access"))
    gate = scorer.run(path, digest, queue_state=queue, gate_only=True)
    assert gate["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    assert gate["final_graph_hashes_sha256"] == config["final_graph_hashes_sha256"]
    assert gate["successor_stage_sha256"] == config["successor_stage_sha256"]
    assert not Path(config["output"]).exists()


@pytest.mark.parametrize("damage", ["successor_receipt", "final_graph_hash"])
def test_successor_tamper_blocks_before_labels(tmp_path, monkeypatch, damage):
    config, path, digest, queue = fixture(tmp_path, monkeypatch)
    if damage == "successor_receipt":
        with Path(config["successor_stage"]).open("a") as stream:
            stream.write(" ")
    else:
        config["final_graph_hashes_sha256"] = "0" * 64
        digest = put(path, config)
    monkeypatch.setattr(scorer, "score_with_labels",
                        lambda *_: pytest.fail("labels opened"))
    with pytest.raises((AssertionError, ValueError)):
        scorer.run(path, digest, queue_state=queue)
    assert not Path(config["output"]).exists()


def test_stopped_coordinator_rejected_and_future_sources_compile():
    with pytest.raises(AssertionError):
        stager.local_gate(stager.STOPPED_COORDINATOR)
    source = launcher.source({"stage": {"manifest_sha256": "a" * 64,
                                       "score_config_sha256": "b" * 64}})
    compile(source, "cpu_launch.py", "exec")
    assert "score_exp227_target6bba_current_v3b.py" in source
    probe = verifier.remote_probe({"stage": {"manifest_sha256": "a" * 64,
                                             "score_config_sha256": "b" * 64},
                                  "config": {"output": verifier.RUN + "/output"}},
                                 {"wrapper_pid": 123})
    compile(probe, "score_readback.py", "exec")


def test_local_stage_binds_successor_and_final_hashes(tmp_path):
    if not stager.LOCAL.exists():
        pytest.skip("Local-only v3b prepare artifact is not present")
    state = json.loads(stager.STOPPED_COORDINATOR.read_text())
    successor = json.loads((stager.BUNDLE / "successor_stage.json").read_text())
    names = state["frozen"]["chunks"][7]
    state["chunks"][7]["stage"] = {"validated": True, "result": successor}
    state["chunks"][7]["launch"] = {"validated": True}
    state["chunks"][7]["postrun"] = {"validated": True,
        "gate": {"chunk_index": 7, "movies": names,
                 "graph_hashes": [{"dataset": name, "csv_sha256": "a" * 64,
                                   "receipt_sha256": "b" * 64} for name in names]}}
    state["status"] = "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED"
    state["movie_count"] = state["graph_count"] = 116
    state["all_leases_released"] = True
    state["target_labels_read"] = state["target_score_computed"] = False
    state["state_sha256"] = scorer.state_digest(state)
    final_path = tmp_path / "new_final_coordinator.json"
    put(final_path, state)
    _, checked, _, bound, graph_sha = stager.local_gate(final_path)
    assert bound == final_path.resolve()
    assert checked["chunks"][7]["stage"]["result"]["lease_id"] == scorer.SUCCESSOR_LEASE
    assert len(graph_sha) == 64


def test_production_successor_identity_is_v2():
    assert scorer.SUCCESSOR_TOKEN == "exp227_target6bba_chunk07_v2_20260927"
    assert scorer.SUCCESSOR_LEASE == "exp227-target6bba-chunk07-v2-20260927"
