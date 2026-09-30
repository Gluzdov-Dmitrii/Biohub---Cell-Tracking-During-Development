"""EXP234 check-only recovery pins the stopped state and writes no receipt."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_exp234_target_official_score_recovery as recovery  # noqa: E402


def test_check_only_keeps_stopped_receipt_and_refuses_changed_source(tmp_path, capsys):
    paths = {key: tmp_path / key for key in ("HANDOFF", "SCORER", "PREPARE", "LAUNCH", "RECEIPT")}
    paths["HANDOFF"].write_text(json.dumps({
        "status": "STOPPED_EXP234_TARGET175_SCORE_HANDOFF", "verify_score_returncode": 1,
        "score_exit": {"returncode": 0, "timeout": False}}))
    paths["SCORER"].write_text("pinned source")
    paths["PREPARE"].write_text("prepared")
    paths["LAUNCH"].write_text("launched")
    expected = {
        "handoff_sha256": recovery.verifier.sha(paths["HANDOFF"]),
        "prepare_sha256": recovery.verifier.sha(paths["PREPARE"]),
        "launch_sha256": recovery.verifier.sha(paths["LAUNCH"]),
        "scorer_source_sha256": recovery.verifier.sha(paths["SCORER"]),
        "gate_sha256": "gate", "result_sha256": "result"}
    checked = {"status": "VERIFIED_EXP234_TARGET175_OFFICIAL",
               "metric_identity": "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY",
               "baseline_replay": "PASS_1e-12", "rows": 175,
               "official_score": 0.7426705533442897,
               "historical_exp214_score": 0.7426705533442897,
               "current_organizer_score": None,
               "gate_sha256": "gate", "result_sha256": "result"}
    with ExitStack() as stack:
        for key in ("HANDOFF", "SCORER"):
            stack.enter_context(patch.object(recovery, key, paths[key]))
        for key in ("PREPARE", "LAUNCH", "RECEIPT"):
            stack.enter_context(patch.object(recovery.verifier, key, paths[key]))
        stack.enter_context(patch.object(recovery, "EXPECTED", expected))
        verify = stack.enter_context(patch.object(recovery.verifier, "verify", return_value=checked))
        recovery.main()
        verify.assert_called_once_with(write_receipt=False)
        assert json.loads(capsys.readouterr().out)["score_receipt_written"] is False
        assert not paths["RECEIPT"].exists()
        assert recovery.verifier.sha(paths["HANDOFF"]) == expected["handoff_sha256"]
        paths["SCORER"].write_text("changed")
        with pytest.raises(AssertionError):
            recovery.main()
        verify.assert_called_once()


def test_write_mode_checks_remote_hashes_then_creates_one_receipt(tmp_path, capsys):
    paths = {key: tmp_path / key for key in ("HANDOFF", "SCORER", "PREPARE", "LAUNCH", "RECEIPT")}
    paths["HANDOFF"].write_text(json.dumps({
        "status": "STOPPED_EXP234_TARGET175_SCORE_HANDOFF", "verify_score_returncode": 1,
        "score_exit": {"returncode": 0, "timeout": False}}))
    for key in ("SCORER", "PREPARE", "LAUNCH"):
        paths[key].write_text(key)
    expected = {"handoff_sha256": recovery.verifier.sha(paths["HANDOFF"]),
                "prepare_sha256": recovery.verifier.sha(paths["PREPARE"]),
                "launch_sha256": recovery.verifier.sha(paths["LAUNCH"]),
                "scorer_source_sha256": recovery.verifier.sha(paths["SCORER"]),
                "gate_sha256": "gate", "result_sha256": "result"}
    checked = {"status": "VERIFIED_EXP234_TARGET175_OFFICIAL",
               "metric_identity": "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY",
               "evidence_class": "Historical EXP214 metric; not current organizer official.",
               "baseline_replay": "PASS_1e-12", "rows": 175,
               "official_score": 0.7426705533442897,
               "historical_exp214_score": 0.7426705533442897,
               "current_organizer_score": None,
               "gate_sha256": "gate", "result_sha256": "wrong"}
    with ExitStack() as stack:
        for key in ("HANDOFF", "SCORER"):
            stack.enter_context(patch.object(recovery, key, paths[key]))
        for key in ("PREPARE", "LAUNCH", "RECEIPT"):
            stack.enter_context(patch.object(recovery.verifier, key, paths[key]))
        stack.enter_context(patch.object(recovery, "EXPECTED", expected))
        verify = stack.enter_context(patch.object(recovery.verifier, "verify", return_value=checked))
        with pytest.raises(AssertionError):
            recovery.main(write_receipt=True)
        assert not paths["RECEIPT"].exists()
        checked["result_sha256"] = "result"
        recovery.main(write_receipt=True)
        emitted = json.loads(capsys.readouterr().out)
        assert emitted["score_receipt_written"] is True
        assert emitted["metric_identity"] == "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY"
        stored = json.loads(paths["RECEIPT"].read_text())
        assert stored["status"] == "VERIFIED_EXP234_TARGET175_OFFICIAL"
        assert stored["evidence_class"] == checked["evidence_class"]
        assert stored["stopped_handoff_sha256"] == expected["handoff_sha256"]
        assert recovery.verifier.sha(paths["HANDOFF"]) == expected["handoff_sha256"]
        with pytest.raises(AssertionError):
            recovery.main(write_receipt=True)
        assert verify.call_count == 2
