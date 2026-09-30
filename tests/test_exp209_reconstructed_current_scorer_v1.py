"""Synthetic EXP209 scorer gates; no GEFF, metric execution, or remote work."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_exp209_reconstructed_scorer_local_v1 as prepare
import score_exp209_reconstructed_current_v1 as scorer
import check_current_organizer_metric_runtime as runtime_check


def put_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived_row(name: str) -> dict:
    return {"dataset": name + ".zarr", "edge_tp": 0, "edge_fp": 0,
            "edge_fn": 0, "division_tp": 0, "division_fp": 0,
            "division_fn": 0, "num_pred_nodes": 1, "node_recall": 1.0,
            "total_node_ratio": 1.0, "edge_jaccard": 0.0,
            "adj_edge_jaccard": 0.0}


def historical_rows() -> dict:
    return {"status": "PASS_FROZEN_CONFIRMATION_ASSEMBLY", "directions": {
        "forward": {"selected_rows": [archived_row(f"6bba_{i:08x}") for i in range(116)]},
        "reverse": {"selected_rows": [archived_row(f"44b6_{i:08x}") for i in range(59)]}}}


def local_prepare_fixture(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    recon = workspace / "work/exp209_current_metric_reconstruction_v1_local_20260927/bundle"
    contract = {"run_root": f"{prepare.REMOTE}/runs/{prepare.RECON_NAME}",
                "code_dir": f"{prepare.REMOTE}/code/{prepare.RECON_NAME}",
                "data_root": f"{prepare.REMOTE}/data/honest195_missing/train"}
    monkeypatch.setattr(prepare, "RECON_BUNDLE_SHA",
                        put_json(recon / "bundle_manifest.json", {"experiment": "synthetic"}))
    monkeypatch.setattr(prepare, "RECON_CONTRACT_SHA",
                        put_json(recon / "contract.json", contract))
    monkeypatch.setattr(prepare, "HISTORICAL_RESULT_SHA",
                        put_json(recon / "historical_result.json", historical_rows()))
    source = workspace / "scripts/synthetic_scorer.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# synthetic scorer source\n")
    monkeypatch.setattr(prepare, "SOURCES", {"synthetic_scorer.py":
                        ("scripts/synthetic_scorer.py", prepare.sha(source))})
    return workspace, recon, source


def test_local_prepare_preflight_seals_sources_without_labels(tmp_path, monkeypatch):
    workspace, _, _ = local_prepare_fixture(tmp_path, monkeypatch)
    bundle = tmp_path / "new_bundle"
    result = prepare.prepare(workspace, bundle)
    assert result["status"] == "PREPARED_EXP209_RECONSTRUCTED_SCORER_V1_LOCAL_ONLY"
    assert result["target_geff_opened"] is False
    assert result["metric_executed"] is False
    assert result["remote_stage_created"] is False
    assert result["remote_run_created"] is False
    assert prepare.sha(bundle / "bundle_manifest.json") == result["bundle_manifest_sha256"]
    assert prepare.sha(bundle / "config.json") == result["config_sha256"]
    assert prepare.sha(bundle / "synthetic_scorer.py") == result["source_hashes"]["synthetic_scorer.py"]
    with pytest.raises(ValueError, match="new and absolute"):
        prepare.prepare(workspace, bundle)


@pytest.mark.parametrize("damage, message", [
    ("manifest", "manifest changed"),
    ("source", "source SHA changed"),
    ("historical_cohort", "selected-row cohort changed"),
])
def test_local_prepare_rejects_tampered_inputs(tmp_path, monkeypatch, damage, message):
    workspace, recon, source = local_prepare_fixture(tmp_path, monkeypatch)
    if damage == "manifest":
        (recon / "bundle_manifest.json").write_bytes(b"changed")
    elif damage == "source":
        source.write_bytes(b"changed source\n")
    else:
        history = historical_rows()
        history["directions"]["reverse"]["selected_rows"].pop()
        monkeypatch.setattr(prepare, "HISTORICAL_RESULT_SHA",
                            put_json(recon / "historical_result.json", history))
    with pytest.raises(ValueError, match=message):
        prepare.prepare(workspace, tmp_path / "new_bundle")


def sealed_synthetic_bundle(tmp_path: Path) -> tuple[Path, str]:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    scorer_path = bundle / "score_exp209_reconstructed_current_v1.py"
    scorer_path.write_bytes(Path(scorer.__file__).read_bytes())
    payload = bundle / "config.json"
    payload.write_bytes(b"{}\n")
    rows = [{"name": path.name, "sha256": scorer.sha(path), "bytes": path.stat().st_size}
            for path in (scorer_path, payload)]
    digest = put_json(bundle / "bundle_manifest.json", {
        "experiment": "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1", "files": rows})
    return bundle, digest


@pytest.mark.parametrize("damage, message", [
    ("manifest", "bundle manifest"),
    ("payload", "bundle file mismatch"),
    ("extra", "file set mismatch"),
])
def test_sealed_bundle_rejects_manifest_payload_and_extra_file(tmp_path, damage, message):
    bundle, digest = sealed_synthetic_bundle(tmp_path)
    assert len(scorer.validate_bundle(bundle, digest)["files"]) == 2
    if damage == "manifest":
        (bundle / "bundle_manifest.json").write_bytes(b"{}\n")
    elif damage == "payload":
        (bundle / "config.json").write_bytes(b"{ }\n")
    else:
        (bundle / "unexpected.py").write_bytes(b"pass\n")
    with pytest.raises(scorer.ScoreError, match=message):
        scorer.validate_bundle(bundle, digest)


def test_historical_selected_rows_and_strict_field_comparison():
    ordered, reference = scorer.historical_selected_rows(historical_rows())
    assert len(ordered) == len(reference) == 175
    assert ordered[0] == "6bba_00000000" and ordered[-1] == "44b6_0000003a"
    expected = reference[ordered[0]]
    scorer.compare_historical_row(dict(expected), expected)
    for field, value in (("edge_tp", 1), ("num_pred_nodes", 1.0),
                         ("node_recall", 1.0 + 2e-12), ("edge_jaccard", float("nan"))):
        actual = dict(expected)
        actual[field] = value
        with pytest.raises(scorer.ScoreError, match="historical replay"):
            scorer.compare_historical_row(actual, expected)
    missing = dict(expected)
    missing.pop("division_fn")
    with pytest.raises(scorer.ScoreError, match="dataset/field"):
        scorer.compare_historical_row(missing, expected)


def test_full_archived_pooled_summary_requires_every_field_with_strict_tolerance():
    expected = {"edge_tp": 10, "edge_fp": 2, "edge_fn": 3,
                "division_tp": 1, "division_fp": 0, "division_fn": 2,
                "n": 175, "edge_jaccard": 0.7, "division_jaccard": 0.25,
                "node_recall": 0.9, "adj_edge_jaccard": 0.72, "score": 0.72}
    scorer.compare_historical_summary(dict(expected), expected)
    for field, value in (("edge_tp", float(expected["edge_tp"])),
                         ("division_fn", expected["division_fn"] + 1),
                         ("score", expected["score"] + 2e-12),
                         ("node_recall", float("nan"))):
        actual = dict(expected)
        actual[field] = value
        with pytest.raises(scorer.ScoreError, match="historical pooled"):
            scorer.compare_historical_summary(actual, expected)
    missing = dict(expected)
    missing.pop("division_jaccard")
    with pytest.raises(scorer.ScoreError, match="summary field mismatch"):
        scorer.compare_historical_summary(missing, expected)


def test_archived_summary_projection_adds_exact_edge_counts_without_metric_execution():
    archived = {"n": 2, "edge_tp": 5, "edge_fp": 2, "edge_fn": 1,
                "division_tp": 0, "division_fp": 0, "division_fn": 1,
                "node_recall": 0.8, "edge_jaccard": 0.625,
                "division_jaccard": 0.0, "adj_edge_jaccard": 0.61,
                "score": 0.61}
    old_summary = {key: value for key, value in archived.items()
                   if key not in {"edge_tp", "edge_fp", "edge_fn"}}
    old_summary["n_adj"] = 2
    rows = [{"edge_tp": 2, "edge_fp": 1, "edge_fn": 0},
            {"edge_tp": 3, "edge_fp": 1, "edge_fn": 1}]
    comparable = scorer.comparable_historical_summary(old_summary, rows, archived)
    assert comparable == archived
    scorer.compare_historical_summary(comparable, archived)


def test_graph_and_receipt_are_both_pinned_before_label_scoring(tmp_path):
    graph = tmp_path / "graph__6bba_00000000.csv"
    receipt = graph.with_suffix(".receipt.json")
    graph.write_bytes(b"canonical graph\n")
    receipt.write_bytes(b'{"shape":[1,4,4,4]}\n')
    expected = {"dataset": "6bba_00000000", "csv_sha256": scorer.sha(graph),
                "receipt_sha256": scorer.sha(receipt)}
    scorer.pinned_graph(graph, expected)
    receipt.write_bytes(b'{"shape":[1,5,4,4]}\n')
    with pytest.raises(scorer.ScoreError, match="graph/receipt changed"):
        scorer.pinned_graph(graph, expected)


def source_replay_fixture(tmp_path: Path, monkeypatch):
    history_path = tmp_path / "historical_result.json"
    put_json(history_path, historical_rows())
    ordered, _ = scorer.historical_selected_rows(historical_rows())
    chunks = [{"name": "forward_00", "direction": "forward", "movies": ordered[:116]},
              {"name": "reverse_00", "direction": "reverse", "movies": ordered[116:]}]
    contract = {"historical_result": str(history_path), "data_root": str(tmp_path / "image_only"),
                "chunks": chunks}
    image_sha = "i" * 64
    coords = np.array([[0.0, 1.0, 1.0, 1.0]])
    gate_rows = []
    for chunk in chunks:
        for name in chunk["movies"]:
            path = scorer.graph_path(tmp_path, chunk, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = io.StringIO(newline="")
            writer = csv.writer(stream)
            writer.writerow(scorer.reconstruction.COLUMNS)
            writer.writerows(scorer.reconstruction.graph_rows(name, coords, []))
            path.write_bytes(stream.getvalue().encode("utf-8"))
            put_json(path.with_suffix(".receipt.json"), {"shape": [1, 4, 4, 4]})
            gate_rows.append({"dataset": name, "image_tree_sha256": image_sha,
                              "nodes": 1, "edges": 0, "csv_sha256": scorer.sha(path)})
    monkeypatch.setattr(scorer.reconstruction, "image_entries", lambda _m, _n: [])
    monkeypatch.setattr(scorer.reconstruction, "image_tree_sha256", lambda *_: image_sha)
    monkeypatch.setattr(scorer.reconstruction, "reconstruct_one",
                        lambda _contract, _chunk, _name, _image_sha:
                        (coords, [], [1, 4, 4, 4], "c" * 64, None))
    return contract, {"graph_hashes": gate_rows}, ordered, chunks


def test_all175_source_telemetry_replays_canonical_csv(tmp_path, monkeypatch):
    contract, gate, ordered, _ = source_replay_fixture(tmp_path, monkeypatch)
    records = scorer.source_telemetry_replay(contract, {}, gate, tmp_path)
    assert len(records) == 175
    assert [row["dataset"] for row in records] == ordered
    assert all(row["historical_source_telemetry"] == "PASS" for row in records)


@pytest.mark.parametrize("damage", ["canonical_csv", "reconstructed_source", "image_sha"])
def test_all175_replay_rejects_graph_or_source_tamper(tmp_path, monkeypatch, damage):
    contract, gate, ordered, chunks = source_replay_fixture(tmp_path, monkeypatch)
    first = ordered[0]
    if damage == "canonical_csv":
        path = scorer.graph_path(tmp_path, chunks[0], first)
        path.write_bytes(path.read_bytes() + b"\n")
        message = "reconstructed graph bytes"
    elif damage == "reconstructed_source":
        coords = np.array([[0.0, 2.0, 1.0, 1.0]])
        monkeypatch.setattr(scorer.reconstruction, "reconstruct_one",
                            lambda _contract, _chunk, _name, _image_sha:
                            (coords, [], [1, 4, 4, 4], "c" * 64, None))
        message = "reconstructed graph bytes"
    else:
        gate["graph_hashes"][0]["image_tree_sha256"] = "0" * 64
        message = "image tree SHA"
    with pytest.raises(scorer.ScoreError, match=message):
        scorer.source_telemetry_replay(contract, {}, gate, tmp_path)


def run_fixture(tmp_path: Path, monkeypatch):
    bundle = tmp_path / "scorer_code"
    bundle.mkdir()
    monkeypatch.setattr(scorer, "__file__", str(bundle / "score_exp209_reconstructed_current_v1.py"))
    config = {"experiment": "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1",
              "scorer_code_dir": str(bundle),
              "reconstruction_gate_sha256": scorer.RECONSTRUCTION_GATE_SHA,
              "reconstruction_bundle_manifest_sha256": scorer.RECONSTRUCTION_BUNDLE_SHA,
              "reconstruction_contract_sha256": scorer.RECONSTRUCTION_CONTRACT_SHA,
              "current_metrics_sha256": scorer.CURRENT_METRICS_SHA,
              "current_division_sha256": scorer.CURRENT_DIVISION_SHA,
              "metric_repo_commit": scorer.ORGANIZER_COMMIT,
              "tracksdata_commit": scorer.TRACKSDATA_COMMIT,
              "output": str(tmp_path / scorer.RUN_NAME)}
    config_path = bundle / "config.json"
    config_sha = put_json(config_path, config)
    monkeypatch.setattr(scorer, "validate_bundle", lambda *_: {})
    monkeypatch.setattr(scorer, "metric_source_gate", lambda *_: None)
    monkeypatch.setattr(runtime_check, "validate_runtime",
                        lambda profile: {"profile": profile, "metadata_only": True})
    hooks = []
    monkeypatch.setattr(scorer.sys, "addaudithook", hooks.append)
    return config_path, config_sha, Path(config["output"]), hooks


def test_label_audit_opens_only_after_durable_gate_and_current_waits_for_replay(tmp_path, monkeypatch):
    config_path, digest, output, hooks = run_fixture(tmp_path, monkeypatch)
    events = []

    def graph_gate(_config):
        events.append("graph_gate")
        with pytest.raises(PermissionError, match="forbids GEFF"):
            hooks[0]("open", (str(tmp_path / "sealed.geff" / "data"), "rb", 0))
        assert not output.exists()
        return {"status": "PASS_NO_LABELS", "labels_read": False}, {}, ["synthetic"], {}

    def historical_replay(path, *_args):
        events.append("historical_replay")
        assert path == output and (path / "no_metric_gate.json").is_file()
        assert scorer.load_json(path / "no_metric_gate.json")["isolated_runtime_metadata"] == {
            "profile": "remote_py311", "metadata_only": True}
        hooks[0]("open", (str(tmp_path / "now_allowed.geff" / "data"), "rb", 0))
        replay = {"status": "PASS_EXP209_RECONSTRUCTED_HISTORICAL175_REPLAY_1E12"}
        scorer.graph_verifier.write_once_durable(path / "historical_replay.json", replay)
        return replay

    def current_score(path, _contract, _ordered, replay, _bundle):
        events.append("current_score")
        assert scorer.load_json(path / "historical_replay.json") == replay
        return {"status": "PASS_SYNTHETIC", "summary": {"score": 0.5}}

    monkeypatch.setattr(scorer, "graph_gate", graph_gate)
    monkeypatch.setattr(scorer, "historical_replay", historical_replay)
    monkeypatch.setattr(scorer, "current_score", current_score)
    assert scorer.run(config_path, digest, "m" * 64)["status"] == "PASS_SYNTHETIC"
    assert events == ["graph_gate", "historical_replay", "current_score"]
    with pytest.raises(scorer.ScoreError, match="new fixed run namespace"):
        scorer.run(config_path, digest, "m" * 64)
    assert events == ["graph_gate", "historical_replay", "current_score"]


def test_historical_replay_failure_seals_block_and_never_calls_current(tmp_path, monkeypatch):
    config_path, digest, output, _ = run_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(scorer, "graph_gate",
                        lambda _config: ({"status": "PASS_NO_LABELS"}, {}, ["synthetic"], {}))

    def reject_replay(*_args):
        assert (output / "no_metric_gate.json").is_file()
        raise scorer.ScoreError("archived row mismatch")

    monkeypatch.setattr(scorer, "historical_replay", reject_replay)
    monkeypatch.setattr(scorer, "current_score",
                        lambda *_args: pytest.fail("current metric ran before historical replay"))
    with pytest.raises(scorer.ScoreError, match="archived row mismatch"):
        scorer.run(config_path, digest, "m" * 64)
    failure = scorer.load_json(output / "historical_replay_failure.json")
    assert failure["status"] == "BLOCKED_EXP209_RECONSTRUCTED_HISTORICAL_REPLAY"
    assert failure["current_metric_executed"] is False
    with pytest.raises(scorer.ScoreError, match="new fixed run namespace"):
        scorer.run(config_path, digest, "m" * 64)
