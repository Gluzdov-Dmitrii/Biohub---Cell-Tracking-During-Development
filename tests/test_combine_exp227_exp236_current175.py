"""Receipt lineage and pooled sufficient-stat gate without remote or labels."""
import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import combine_exp227_exp236_current175 as pooled  # noqa: E402


def synthetic():
    folds, archive, baseline, assignment = pooled.local_inputs()
    summarise = pooled.organizer_summarise()
    remote = {}
    for name, fold in folds.items():
        config = fold["stage"]["config"]
        historical = [copy.deepcopy(archive[movie]) for movie in fold["ids"]]
        current_base = copy.deepcopy(historical)
        candidate = copy.deepcopy(historical)
        for row in candidate:
            row["adj_edge_jaccard"] += 0.001
        old_summary = summarise(current_base)
        new_summary = summarise(candidate)
        fold["verified"] = dict(fold["verified"],
                                baseline_score=old_summary["score"],
                                official_score=new_summary["score"],
                                delta_vs_current_baseline=new_summary["score"] - old_summary["score"])
        gate = {"status": fold["spec"]["gate_status"],
                "candidate_count": fold["spec"]["n"],
                "baseline_count": fold["spec"]["n"],
                "target_labels_read": False,
                "graph_hashes": fold["graph_hashes"],
                "baseline_hashes": config["baseline_input_hashes"],
                "coordinator_sha256": config["coordinator_sha256"],
                "current_metrics_sha256": pooled.METRIC_SHA,
                "current_division_sha256": pooled.DIVISION_SHA,
                "tracksdata_commit": pooled.TRACKSDATA_COMMIT,
                "live_release": [{"state": "RELEASED"} for _ in fold["coordinator"]["chunks"]]}
        result = {"status": fold["spec"]["result_status"],
                  "baseline_replay": "PASS_1e-12",
                  "target_labels_read_after_graph_gate": True,
                  "evidence_class": pooled.EVIDENCE_CLASS,
                  "no_metric_gate_sha256": fold["verified"]["gate_sha256"],
                  "label_tree_hashes_sha256": "f" * 64,
                  "metric_source": "current organizer commit " + pooled.METRIC_COMMIT,
                  "current_metrics_sha256": pooled.METRIC_SHA,
                  "current_division_sha256": pooled.DIVISION_SHA,
                  "legacy_exp214_baseline_rows": historical,
                  "baseline_rows": current_base, "candidate_rows": candidate,
                  "baseline_summary": old_summary, "candidate_summary": new_summary}
        remote[name] = {"config": config, "gate": gate, "result": result,
                        "manifest_sha256": fold["stage"]["stage"]["manifest_sha256"],
                        "config_sha256": fold["stage"]["stage"]["score_config_sha256"],
                        "gate_sha256": fold["verified"]["gate_sha256"],
                        "result_sha256": fold["verified"]["result_sha256"],
                        "label_tree_hashes_sha256": "f" * 64}
    return folds, archive, baseline, assignment, remote, summarise


def test_exact_local_receipts_and_175_disjoint_ids():
    folds, archive, baseline, assignment = pooled.local_inputs()
    forward = folds["exp227_target6bba"]["ids"]
    reverse = folds["exp236_target44b6"]["ids"]
    assert len(forward) == 116 and len(reverse) == 59
    assert not set(forward).intersection(reverse)
    assert set(forward) | set(reverse) == set(archive)
    assert pooled.sha(pooled.METRIC_SOURCE) == pooled.METRIC_SHA
    assert baseline["summary"]["public"]["score"] == pytest.approx(pooled.EXP214_SCORE)


def test_pooled_organizer_summarise_uses_all_rows_not_fold_score_average():
    folds, archive, baseline, assignment, remote, summarise = synthetic()
    receipt = pooled.combine(folds, archive, baseline, assignment, remote, summarise)
    assert receipt["movie_count"] == 175
    assert receipt["score"] == pytest.approx(pooled.EXP214_SCORE + 0.001)
    assert receipt["delta_vs_exp214_paired"] == pytest.approx(0.001)
    assert receipt["exp209_reconstructed_score"] == pooled.EXP209_SCORE
    assert receipt["target_geff_read_by_combiner"] is False
    assert receipt["remote_mutation"] is False
    fold_mean = sum(folds[name]["verified"]["official_score"] * folds[name]["spec"]["n"]
                    for name in folds) / 175
    assert abs(receipt["score"] - fold_mean) > 0.001


@pytest.mark.parametrize("damage", ["graph_hash", "duplicate_id", "legacy_row", "metric_source"])
def test_tamper_fails_before_pooled_result(damage):
    folds, archive, baseline, assignment, remote, summarise = synthetic()
    payload = remote["exp227_target6bba"]
    if damage == "graph_hash":
        payload["gate"]["graph_hashes"] = copy.deepcopy(payload["gate"]["graph_hashes"])
        payload["gate"]["graph_hashes"][0]["csv_sha256"] = "0" * 64
    elif damage == "duplicate_id":
        payload["result"]["candidate_rows"][0]["dataset"] = (
            payload["result"]["candidate_rows"][1]["dataset"])
    elif damage == "legacy_row":
        payload["result"]["legacy_exp214_baseline_rows"][0]["edge_tp"] += 1
    else:
        payload["result"]["metric_source"] = "stale metric"
    with pytest.raises(ValueError):
        pooled.combine(folds, archive, baseline, assignment, remote, summarise)


def test_absent_verification_blocks_before_ssh(tmp_path, monkeypatch):
    specs = copy.deepcopy(pooled.FOLDS)
    specs["exp227_target6bba"]["verify"] = tmp_path / "absent.json"
    monkeypatch.setattr(pooled, "FOLDS", specs)
    monkeypatch.setattr(pooled, "fetch_remote", lambda _: pytest.fail("SSH before receipt"))
    with pytest.raises(FileNotFoundError):
        pooled.run()


def test_remote_probe_is_json_only_and_compiles():
    specs = {"fold": {"code": "/exact/code", "output": "/exact/output",
                       "manifest_sha": "a" * 64, "config_sha": "b" * 64,
                       "gate_sha": "c" * 64, "result_sha": "d" * 64}}
    source = pooled.remote_probe_source(specs)
    compile(source, "pooled_remote_probe", "exec")
    assert ".geff" not in source.lower()
    assert ".write" not in source
    assert "result.json" in source and "no_metric_gate.json" in source
