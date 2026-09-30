"""Current organizer rescore stays behind a sealed graph and runtime gate."""
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_exp234_current_organizer as prepare  # noqa: E402
import score_exp234_current_organizer as scorer  # noqa: E402


def test_prelabel_gate_refuses_changed_historical_gate_before_scoring(tmp_path):
    old_code = tmp_path / "old_code"
    old_code.mkdir()
    hist_config = tmp_path / "old_config.json"
    hist_config.write_text(json.dumps({"cohort_sha256": "cohort"}))
    old_gate = {"status": "PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS",
                "candidate_count": 175, "baseline_count": 175,
                "prediction_hashes": [{} for _ in range(12)],
                "baseline_hashes": [{} for _ in range(8)]}
    gate_path = tmp_path / "no_metric_gate.json"
    gate_path.write_text(json.dumps(old_gate))
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps({
        "status": "PASS_EXP234_SOURCE_SELECTED_TARGET175",
        "no_metric_gate_sha256": scorer.sha(gate_path)}))
    names = {f"44b6_{i:08x}" for i in range(59)} | {f"6bba_{i:08x}" for i in range(116)}
    graphs = {name: {} for name in names}
    cohort = {name: {} for name in names}
    config = {"experiment": "EXP234_CURRENT_ORGANIZER_TARGET175_V1",
              "organizer_commit": scorer.ORGANIZER_COMMIT,
              "tracksdata_commit": scorer.TRACKSDATA_COMMIT,
              "metric_sha256": scorer.METRIC_SHA256,
              "code": str(tmp_path / "new_code"), "code_manifest_sha256": "new_manifest",
              "historical_code": str(old_code), "historical_manifest_sha256": "old_manifest",
              "historical_scorer_sha256": "sealed_scorer",
              "historical_config": str(hist_config),
              "historical_config_sha256": scorer.sha(hist_config),
              "historical_gate": str(gate_path), "historical_gate_sha256": scorer.sha(gate_path),
              "historical_result": str(result_path),
              "historical_result_sha256": scorer.sha(result_path)}
    manifests = {str(tmp_path / "new_code"):
                 {"score_exp234_current_organizer.py": scorer.sha(Path(scorer.__file__))},
                 str(old_code): {"score_exp234_target_official.py": "sealed_scorer"}}
    with patch.object(scorer, "pinned_manifest", side_effect=lambda code, _: manifests[str(code)]), \
         patch.object(scorer, "load_historical_gate", return_value=lambda _: (
             cohort, graphs, graphs, {}, {}, old_gate)) as loaded, \
         patch.object(scorer, "validate_runtime", return_value={"profile": "remote_py311"}), \
         patch.object(scorer, "load_metric", return_value=object()), \
         patch.object(scorer, "synthetic_contract", return_value={"status": "PASS"}), \
         patch.object(scorer, "image_metadata", return_value=[]):
        assert scorer.prelabel_gate(config)[-1]["candidate_count"] == 175
        assert loaded.call_count == 1
        gate_path.write_text(json.dumps({**old_gate, "altered": True}))
        with pytest.raises(AssertionError):
            scorer.prelabel_gate(config)
        assert loaded.call_count == 1


def test_geff_tree_digest_detects_byte_change(tmp_path):
    geff = tmp_path / "movie.geff"
    geff.mkdir()
    (geff / "zarr.json").write_text("{}")
    (geff / "c").mkdir()
    payload = geff / "c" / "0"
    payload.write_bytes(b"first")
    first = scorer.tree_hash(geff)
    payload.write_bytes(b"second")
    second = scorer.tree_hash(geff)
    assert first["files"] == second["files"] == 2
    assert first["sha256"] != second["sha256"]


def test_local_prepare_is_one_shot_and_separates_outputs(tmp_path):
    bundle, receipt = tmp_path / "bundle", tmp_path / "prepare.json"
    prepared = prepare.prepare(bundle=bundle, receipt=receipt)
    assert prepared["remote_staged"] is False and prepared["target_labels_read"] is False
    config = json.loads((bundle / "score_config.json").read_text())
    manifest = json.loads((bundle / "code_manifest.json").read_text())
    assert config["code_manifest_sha256"] == scorer.sha(bundle / "code_manifest.json")
    assert manifest["tracking_cellmot_official/metrics.py"] == scorer.METRIC_SHA256["metrics.py"]
    assert config["output"] != config["historical_run"] + "/output"
    assert config["python"] == prepare.REMOTE_PYTHON
    with pytest.raises(AssertionError):
        prepare.prepare(bundle=bundle, receipt=receipt)


def test_pinned_synthetic_local_fork_contract():
    python = ROOT / "work/x138_provenance/official_metric/venv/Scripts/python.exe"
    completed = subprocess.run([
        str(python), str(ROOT / "scripts/check_current_organizer_metric_runtime.py"),
        "--profile", "local_contract_py312",
        "--package-root", str(ROOT / "work/x138_provenance/official_metric")],
        capture_output=True, text=True, check=True, timeout=60)
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"
    assert result["positive_division"] == [1, 0, 0]
    assert result["remote_weak_component_division"] == [0, 0, 1]
