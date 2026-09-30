"""Narrow checks for the one-shot current metric handoff controls."""
import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_exp234_current_organizer as verify  # noqa: E402


def test_receipt_chain_and_remote_verifier_source(monkeypatch):
    prepared = json.loads(verify.PREPARE.read_text())
    staged = json.loads(verify.STAGE.read_text())
    runtime = json.loads(verify.ENV_VERIFY.read_text())
    launched = json.loads(verify.LAUNCH.read_text())
    assert staged["prepare_sha256"] == verify.sha(verify.PREPARE)
    assert runtime["stage_sha256"] == verify.sha(verify.STAGE)
    assert launched["env_verify_sha256"] == verify.sha(verify.ENV_VERIFY)
    assert staged["stage"]["source_hashes"] == prepared["source_hashes"]
    assert launched["launch"]["kaggle_post"] is False
    never_write = ROOT / "reports/_test_exp234_current_no_write.json"
    assert not never_write.exists()
    monkeypatch.setattr(verify, "RECEIPT", never_write)

    class SourceParsed(Exception):
        pass

    def inspect_remote(source, interpreter):
        assert interpreter == prepared["interpreter_intended"]
        ast.parse(source)
        assert "target_labels_read_after_gate" in source
        assert "label_tree_hashes.json" in source
        raise SourceParsed

    monkeypatch.setattr(verify, "remote", inspect_remote)
    with pytest.raises(SourceParsed):
        verify.main()
    assert not verify.RECEIPT.exists()


def test_original_stopped_receipt_and_separate_current_run():
    prepared = json.loads(verify.PREPARE.read_text())
    original = ROOT / "reports/exp234_target_score_handoff_20260927.json"
    assert verify.sha(original) == prepared["prerequisite_local_sha256"][
        "reports/exp234_target_score_handoff_20260927.json"]
    assert json.loads(original.read_text())["status"].startswith("STOPPED")
    config = json.loads((ROOT / "work/exp234_current_organizer_v1/score_config.json").read_text())
    assert config["run"] != config["historical_run"]
    assert config["output"] != config["historical_run"] + "/output"
