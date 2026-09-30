"""The EXP227 v3 current scorer preserves the complete frozen 116-graph gate."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import score_exp227_target6bba_official as old
import score_exp227_target6bba_current_v3 as current
import launch_exp227_target6bba_scorer_v3 as launcher
import verify_exp227_target6bba_scorer_v3 as verifier
from test_exp227_target6bba_official_scorer import fixture as frozen_fixture, put, write, csv_rows


def fixture(tmp_path, monkeypatch):
    config, path, _, queue, root = frozen_fixture(tmp_path, monkeypatch)
    for key in ("REMOTE", "ASSIGNMENT_SHA", "CHECKPOINT_SHA", "COHORT_SHA",
                "BASELINE_SHA", "CURRENT_METRICS_SHA", "CURRENT_DIVISION_SHA"):
        monkeypatch.setattr(current, key, getattr(old, key))
    config["experiment"] = "EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3"
    baseline = json.loads(Path(config["baseline_metrics"]).read_text())
    source = [f"44b6_{i:08x}" for i in range(59)]
    target_names = config["target_ids"]
    groups = [source[0:12], source[12:24], source[24:36], source[36:48], source[48:59],
              target_names[0:39], target_names[39:78], target_names[78:116]]
    parts = []
    for i, names in enumerate(groups):
        marker = "44b6" if i < 5 else "6bba"
        csv_path = tmp_path / f"exp214_{marker}_{i}" / "submission.csv"
        csv_sha = write(csv_path, csv_rows(names))
        receipt_sha = put(csv_path.parent / "inference_receipt.json",
                          {"submission_sha256": csv_sha, "movies": names})
        parts.append({"csv": str(csv_path), "sha256": csv_sha,
                      "receipt_sha256": receipt_sha})
    baseline["input_hashes"]["public"] = parts
    config["baseline_metrics_sha256"] = put(Path(config["baseline_metrics"]), baseline)
    monkeypatch.setattr(current, "BASELINE_SHA", config["baseline_metrics_sha256"])
    config["baseline_input_hashes"] = baseline["input_hashes"]["public"]
    target = [row for row in baseline["rows"]["public"]
              if row["dataset"] in set(config["target_ids"])]
    config["baseline_target_rows_sha256"] = hashlib.sha256(json.dumps(target,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    config["tracksdata_commit"] = current.TRACKSDATA_COMMIT
    config["image_scale_audit_sha256"] = current.IMAGE_AUDIT_SHA
    config["python"] = sys.executable
    monkeypatch.setattr(current, "current_import_gate", lambda _: ({"profile": "fake"},
                         {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"}))
    monkeypatch.setattr(current, "image_metadata", lambda _, __, names: [
        {"dataset": name, "scale": [1.625, 0.40625, 0.40625]} for name in names])
    digest = put(path, config)
    return config, path, digest, queue, root


def test_full_116_gate_then_durable_label_order(tmp_path, monkeypatch):
    config, path, digest, queue, _ = fixture(tmp_path, monkeypatch)
    gate = current.run(path, digest, queue_state=queue, gate_only=True)
    assert gate["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    assert gate["candidate_count"] == gate["baseline_count"] == 116
    assert len(gate["image_metadata"]) == 116
    assert not Path(config["output"]).exists()
    monkeypatch.setattr(current, "label_manifest", lambda *_: {"fake": "hash"})

    def labels(cfg, *_):
        assert json.loads((Path(cfg["output"]) / "no_metric_gate.json").read_text())[
            "target_labels_read"] is False
        return [], [], [], {"score": 0.4}, {"score": 0.5}, {"score": 0.6}

    monkeypatch.setattr(current, "score_with_labels", labels)
    result = current.run(path, digest, queue_state=queue)
    assert result["status"] == "PASS_EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3"
    assert result["delta_vs_current_baseline"] == pytest.approx(0.1)


@pytest.mark.parametrize("damage", ["running_lease", "csv_tamper", "baseline_rows",
                                      "metric_hash"])
def test_tamper_blocks_before_labels(tmp_path, monkeypatch, damage):
    config, path, digest, queue, root = fixture(tmp_path, monkeypatch)
    if damage == "running_lease":
        queue["requests"][0]["state"] = "RUNNING"
    elif damage == "csv_tamper":
        graph = next((root / "runs/exp227_target6bba_chunk00_v1_20260927/output").glob("*.csv"))
        graph.write_text(graph.read_text() + "junk\n")
    elif damage == "baseline_rows":
        config["baseline_target_rows_sha256"] = "0" * 64
        digest = put(path, config)
    else:
        config["current_metrics_sha256"] = "0" * 64
        digest = put(path, config)
    monkeypatch.setattr(current, "score_with_labels",
                        lambda *_: pytest.fail("labels opened before no-label gate"))
    with pytest.raises((AssertionError, ValueError)):
        current.run(path, digest, queue_state=queue)
    assert not Path(config["output"]).exists()


def test_generated_cpu_launch_and_verifier_sources_compile():
    source = launcher.source({"stage": {"manifest_sha256": "a" * 64,
                                       "score_config_sha256": "b" * 64}})
    compile(source, "remote_cpu_launch.py", "exec")
    assert "current-organizer-py311-e13cf-v1" in launcher.PYTHON
    assert "score_exp227_target6bba_current_v3.py" in source
    probe = verifier.remote_probe({"stage": {"manifest_sha256": "a" * 64,
                                             "score_config_sha256": "b" * 64},
                                  "config": {"output": verifier.RUN + "/output"}},
                                 {"wrapper_pid": 123})
    compile(probe, "remote_verify.py", "exec")
