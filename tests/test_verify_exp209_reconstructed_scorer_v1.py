"""Synthetic, label-free checks for EXP209 scorer completion verification."""

import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_exp209_reconstructed_scorer_v1 as verify  # noqa: E402


def historical_fixture():
    counts = {key: 1 for key in verify.OLD_COUNTS}
    floats = {key: 0.5 for key in verify.OLD_FLOATS}
    old_forward = [{"dataset": f"6bba_{n:04d}.zarr", **counts, **floats}
                   for n in range(116)]
    old_reverse = [{"dataset": f"44b6_{n:04d}.zarr", **counts, **floats}
                   for n in range(59)]
    ordered = [row["dataset"][:-5] for row in old_forward + old_reverse]
    rows = [{**row, "dataset": row["dataset"][:-5]}
            for row in old_forward + old_reverse]
    projected = {"n": 175, "score": verify.HISTORICAL_SCORE,
                 "edge_tp": 175, "edge_fp": 175, "edge_fn": 175}
    archive = {"directions": {"forward": {"selected_rows": old_forward},
                               "reverse": {"selected_rows": old_reverse}},
               "combined": {"frozen_selected": projected}}
    replay = {"rows": rows, "summary": {"n": 175,
                                          "score": verify.HISTORICAL_SCORE},
              "archived_comparable_summary": projected,
              "archived_exp209_score": verify.HISTORICAL_SCORE}
    return archive, replay, ordered


def test_all175_historical_row_and_pooled_replay_requires_actual_values():
    archive, replay, ordered = historical_fixture()
    verify.compare_historical(archive, replay, ordered)
    changed = copy.deepcopy(replay)
    changed["rows"][91]["adj_edge_jaccard"] += 1e-7
    with pytest.raises(RuntimeError, match="adj_edge_jaccard"):
        verify.compare_historical(archive, changed, ordered)
    changed = copy.deepcopy(replay)
    changed["archived_comparable_summary"]["edge_tp"] = 176
    with pytest.raises(RuntimeError, match="historical pooled edge_tp"):
        verify.compare_historical(archive, changed, ordered)
    changed = copy.deepcopy(replay)
    changed["summary"]["score"] += 1e-7
    with pytest.raises(RuntimeError, match="historical pooled"):
        verify.compare_historical(archive, changed, ordered)


def test_reviewed_local_stage_and_launch_sha_pins(monkeypatch):
    params = verify.local_parameters()
    assert params["stage_receipt_sha256"] == verify.STAGE_RECEIPT_SHA
    assert params["launch_receipt_sha256"] == verify.LAUNCH_RECEIPT_SHA
    monkeypatch.setattr(verify, "LAUNCH_RECEIPT_SHA", "0" * 64)
    with pytest.raises(RuntimeError, match="SHA mismatch"):
        verify.local_parameters()


def test_unfinished_and_failed_workers_never_yield_a_score(monkeypatch, tmp_path):
    params = copy.deepcopy(verify.local_parameters())
    base = tmp_path / "remote"
    code = base / "code" / verify.NAME
    control = base / "runs" / ("." + verify.NAME + ".control")
    run = base / "runs" / verify.NAME
    code.mkdir(parents=True)
    control.mkdir(parents=True)
    for key, value in (("CODE", code), ("CONTROL", control), ("RUN", run)):
        monkeypatch.setattr(verify, key, value.as_posix())
    params["stage"]["code_dir"] = code.as_posix()
    params["stage"]["run_root"] = run.as_posix()
    params["launch"]["control_dir"] = control.as_posix()
    params["launch"]["run_root"] = run.as_posix()
    params["launch"]["worker_pid"] = 999999999
    params["launch"]["supervisor_pid"] = 999999998
    pending = verify.remote_verify(params)
    assert pending["status"] == "RUNNING_EXP209_SCORER_V1_NO_RESULT_CLAIM"
    assert pending["completion_absent"] is True
    assert "current_score" not in pending
    (control / "completion.json").write_text(json.dumps({"status": "FAILED_EXP209_SCORER_V1",
        "exit_code": 1, "timed_out": False, "worker_absent": True}))
    failed = verify.remote_verify(params)
    assert failed["status"] == "FAILED_EXP209_SCORER_V1_NO_VERIFIED_SCORE"
    assert "current_score" not in failed


def test_nonfinite_receipts_and_logs_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"score": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="nonfinite"):
        verify.load(bad)
    assert verify.finite_tree({"rows": [{"score": float("inf")} ]}) is False
    with pytest.raises(ValueError, match="nonfinite"):
        verify.load_last_json(['{"status": "PASS", "score": Infinity}'])
