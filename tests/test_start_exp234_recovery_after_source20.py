"""Local-only contracts for the finite EXP234 source20 release starter."""
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import start_exp234_recovery_after_source20 as starter  # noqa: E402


def source_state(status):
    result = {"status": status, "target_labels_opened": False,
              "source_labels_opened_before_inference": False,
              "training_run": starter.source20.TRAIN_RUN,
              "source_graph_run": starter.source20.GRAPH_RUN,
              "source_score_run": starter.source20.SCORE_RUN}
    if status == starter.SOURCE_PASS:
        result["finished_or_stopped"] = 10
    return result


def graph_observation():
    names = list(starter.source20.INNER_IDS)
    return {"exit": {"returncode": 0, "hard_timeout": False},
            "status": "PASS_EXP227_SOURCE_GRAPH20_NO_LABELS",
            "source_labels_read": False, "target_labels_read": False,
            "movies": names, "records": 8,
            "complete_status": "RELEASED_AFTER_VERIFIED_EXIT",
            "control_state": "RELEASED",
            "output_names": ["status.json"] + [
                "graph__" + name + suffix for name in names
                for suffix in (".csv", ".json")]}


def write(path, value):
    path.write_text(json.dumps(value))


def local_paths(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(starter, "ROOT", tmp_path)
    monkeypatch.setattr(starter, "RECEIPT", reports / "starter.json")
    monkeypatch.setattr(starter.source20, "RECEIPT", reports / "source20.json")
    monkeypatch.setattr(starter.source20, "SCORE_VERIFIED", reports / "source20_score.json")
    monkeypatch.setattr(starter.source20, "GRAPH_CONFIG", reports / "source20_graph_config.json")
    monkeypatch.setattr(starter.recovery, "ORIGINAL", reports / "original.json")
    monkeypatch.setattr(starter.recovery, "RECEIPT", reports / "recovery.json")
    monkeypatch.setattr(starter.scorer, "RECEIPT", reports / "scorer.json")
    for name in ("RELEASE", "SCORE_PREPARE", "SCORE_LAUNCH", "SCORE_VERIFIED"):
        monkeypatch.setattr(starter.scorer, name, reports / (name.lower() + ".json"))
    write(starter.recovery.ORIGINAL, {"status": "STOPPED_EXP234_TARGET_ROLLOUT",
                                      "completed": [{"source": "6bba", "chunk": i} for i in range(4)] +
                                                   [{"source": "44b6", "chunk": 0}]})
    return reports


@pytest.mark.parametrize("status", [None, "STOPPED_EXP227_SOURCE20_HANDOFF"])
def test_absent_or_stopped_source_blocks_claim_and_any_child(tmp_path, monkeypatch, status):
    local_paths(tmp_path, monkeypatch)
    if status:
        write(starter.source20.RECEIPT, source_state(status))
    calls = []
    monkeypatch.setattr(starter.subprocess, "Popen", lambda *_a, **_k: calls.append(1))
    with pytest.raises(starter.TerminalAnomaly):
        starter.main()
    assert not starter.RECEIPT.exists()
    assert calls == []


def test_fresh_graph_release_requires_embedded_and_live_released_state(tmp_path, monkeypatch):
    local_paths(tmp_path, monkeypatch)
    write(starter.source20.SCORE_VERIFIED,
          {"status": "VERIFIED_EXP227_SOURCE20_OFFICIAL", "rows": 8,
           "source_labels_read": True, "target_labels_read": False,
           "source_score": 0.82})
    write(starter.source20.GRAPH_CONFIG,
          {"run": starter.source20.GRAPH_RUN, "alias": "nsu-a100"})
    observed = source_state(starter.SOURCE_PASS)
    observed["graph_release_or_exit"] = [{"state": "RELEASED"}, graph_observation()]
    observed["source_score_receipt"] = str(starter.source20.SCORE_VERIFIED)
    write(starter.source20.RECEIPT, observed)
    monkeypatch.setattr(starter.source20, "queue_lease",
                        lambda *_args: {"state": "RELEASED"})
    monkeypatch.setattr(starter.source20, "probe_gpu_run",
                        lambda *_args: graph_observation())
    gate = starter.verify_source_graph_release(observed)
    assert gate["graph_lease_state"] == "RELEASED" and gate["graph_movies"] == 8
    monkeypatch.setattr(starter.source20, "queue_lease",
                        lambda *_args: {"state": "RUNNING"})
    with pytest.raises(starter.TerminalAnomaly, match="independently released"):
        starter.verify_source_graph_release(observed)
    observed["graph_release_or_exit"] = [{"state": "RUNNING"}, graph_observation()]
    with pytest.raises(starter.TerminalAnomaly, match="verified graph release"):
        starter.verify_source_graph_release(observed)


def test_waiting_source_then_one_hidden_recovery_and_scorer(tmp_path, monkeypatch):
    reports = local_paths(tmp_path, monkeypatch)
    write(starter.source20.RECEIPT,
          source_state("WAITING_FOR_EXP227_BLOCK03_RELEASE"))
    events = []
    monkeypatch.setattr(starter, "source_process_create_time", lambda: 123.0)

    def finish_source(_seconds):
        events.append("source_pass")
        write(starter.source20.RECEIPT, source_state(starter.SOURCE_PASS))

    monkeypatch.setattr(starter.time, "sleep", finish_source)

    def verify(observed):
        assert observed["status"] == starter.SOURCE_PASS
        events.append("graph_release")
        return {"graph_lease_state": "RELEASED"}

    monkeypatch.setattr(starter, "verify_source_graph_release", verify)
    monkeypatch.setattr(starter.recovery, "original_prefix", lambda: (
        events.append("five_chunk_audit") or starter.read_json(starter.recovery.ORIGINAL),
        {}, {}, {"stage": {"manifest_sha256": "manifest"}}))

    class FakeProcess:
        def __init__(self, pid):
            self.pid = pid

        def poll(self):
            return None

    def fake_popen(args, **kwargs):
        assert args[0] == sys.executable and len(args) == 2
        assert Path(args[1]) in (starter.RECOVERY_SCRIPT, starter.SCORER_SCRIPT)
        assert " " in args[1]  # The argv list preserves the workspace path.
        assert kwargs["cwd"] == tmp_path
        assert kwargs["creationflags"] == getattr(starter.subprocess, "CREATE_NO_WINDOW", 0)
        if Path(args[1]) == starter.RECOVERY_SCRIPT:
            assert events == ["source_pass", "graph_release", "five_chunk_audit"]
            events.append("recovery")
            pid = 1001
            write(starter.recovery.RECEIPT,
                  {"status": "WAITING_FOR_FAIR_A100_FOR_EXP234_TARGET_RECOVERY",
                   "pid": pid, "target_labels_read": False, "kaggle_post": False,
                   "original_coordinator_sha256": starter.sha(starter.recovery.ORIGINAL),
                   "completed": starter.read_json(starter.recovery.ORIGINAL)["completed"]})
        else:
            assert starter.recovery.RECEIPT.exists()
            events.append("scorer")
            pid = 1002
            write(starter.scorer.RECEIPT,
                  {"status": "WAITING_FOR_EXP234_TARGET175_RECOVERY_NO_LABEL_RELEASE",
                   "coordinator_receipt": str(starter.recovery.RECEIPT),
                   "target_labels_opened_before_graph_gate": False,
                   "kaggle_post": False})
        return FakeProcess(pid)

    monkeypatch.setattr(starter.subprocess, "Popen", fake_popen)
    starter.main()
    saved = starter.read_json(starter.RECEIPT)
    assert events == ["source_pass", "graph_release", "five_chunk_audit",
                      "recovery", "scorer"]
    assert saved["status"] == "PASS_EXP234_SOURCE20_RELEASE_CONTROLLERS_STARTED"
    assert saved["recovery_pid"] == 1001 and saved["scorer_pid"] == 1002
    assert saved["recovery_start_attempted"] and saved["scorer_start_attempted"]
    assert (reports / "exp234_target_recovery_v2_20260927.stdout.log").exists()
    with pytest.raises(starter.TerminalAnomaly, match="Existing starter receipt"):
        starter.main()


@pytest.mark.parametrize("partial", ["recovery_receipt", "scorer_log", "score_prepare"])
def test_preexisting_child_or_partial_start_blocks_duplicate(tmp_path, monkeypatch, partial):
    local_paths(tmp_path, monkeypatch)
    write(starter.source20.RECEIPT, source_state(starter.SOURCE_PASS))
    path = {"recovery_receipt": starter.recovery.RECEIPT,
            "scorer_log": starter.child_files("scorer")[0],
            "score_prepare": starter.scorer.SCORE_PREPARE}[partial]
    path.write_text("partial")
    with pytest.raises(starter.TerminalAnomaly, match="Existing EXP234"):
        starter.main()
    assert not starter.RECEIPT.exists()


def test_partial_recovery_start_stops_without_scorer_or_retry(tmp_path, monkeypatch):
    local_paths(tmp_path, monkeypatch)
    write(starter.source20.RECEIPT, source_state(starter.SOURCE_PASS))
    monkeypatch.setattr(starter, "verify_source_graph_release", lambda _state: {})
    monkeypatch.setattr(starter.recovery, "original_prefix", lambda: (
        starter.read_json(starter.recovery.ORIGINAL), {}, {},
        {"stage": {"manifest_sha256": "manifest"}}))
    calls = []

    class ExitedProcess:
        pid = 1001

        def poll(self):
            return 1

    def fake_popen(args, **_kwargs):
        calls.append(args)
        return ExitedProcess()

    monkeypatch.setattr(starter.subprocess, "Popen", fake_popen)
    with pytest.raises(starter.TerminalAnomaly, match="before receipt"):
        starter.main()
    saved = starter.read_json(starter.RECEIPT)
    assert saved["status"] == "STOPPED_EXP234_SOURCE20_RELEASE_STARTER"
    assert saved["recovery_start_attempted"] and not saved["scorer_start_attempted"]
    assert len(calls) == 1 and not starter.scorer.RECEIPT.exists()
    assert starter.child_files("recovery")[0].exists()
    with pytest.raises(starter.TerminalAnomaly, match="Existing starter receipt"):
        starter.main()


@pytest.mark.parametrize("second", ["bad_recovery_pid", "scorer_exits_without_receipt"])
def test_recovery_readback_or_scorer_partial_start_stops_once(tmp_path, monkeypatch, second):
    local_paths(tmp_path, monkeypatch)
    write(starter.source20.RECEIPT, source_state(starter.SOURCE_PASS))
    monkeypatch.setattr(starter, "verify_source_graph_release", lambda _state: {})
    monkeypatch.setattr(starter.recovery, "original_prefix", lambda: (
        starter.read_json(starter.recovery.ORIGINAL), {}, {},
        {"stage": {"manifest_sha256": "manifest"}}))
    calls = []

    class FakeProcess:
        def __init__(self, pid, exit_code):
            self.pid = pid
            self.exit_code = exit_code

        def poll(self):
            return self.exit_code

    def fake_popen(args, **_kwargs):
        calls.append(Path(args[1]).name)
        if Path(args[1]) == starter.RECOVERY_SCRIPT:
            write(starter.recovery.RECEIPT,
                  {"status": "WAITING_FOR_FAIR_A100_FOR_EXP234_TARGET_RECOVERY",
                   "pid": 1002 if second == "bad_recovery_pid" else 1001,
                   "target_labels_read": False, "kaggle_post": False,
                   "original_coordinator_sha256": starter.sha(starter.recovery.ORIGINAL),
                   "completed": starter.read_json(starter.recovery.ORIGINAL)["completed"]})
            return FakeProcess(1001, None)
        assert starter.recovery.RECEIPT.exists()
        return FakeProcess(1002, 1)

    monkeypatch.setattr(starter.subprocess, "Popen", fake_popen)
    with pytest.raises(starter.TerminalAnomaly):
        starter.main()
    result = starter.read_json(starter.RECEIPT)
    assert result["status"] == "STOPPED_EXP234_SOURCE20_RELEASE_STARTER"
    assert result["recovery_start_attempted"] is True
    assert result["scorer_start_attempted"] is (second == "scorer_exits_without_receipt")
    assert calls == ([starter.RECOVERY_SCRIPT.name] if second == "bad_recovery_pid"
                     else [starter.RECOVERY_SCRIPT.name, starter.SCORER_SCRIPT.name])
    assert not starter.scorer.RECEIPT.exists()
