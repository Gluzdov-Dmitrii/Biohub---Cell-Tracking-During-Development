"""The official scorer must refuse chunks without verified lease release."""
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_exp234_target_official import released


def test_exp234_official_requires_verified_release(tmp_path):
    code = tmp_path / "code"
    run = tmp_path / "run"
    run.mkdir()
    plan = code / "44b6_chunk00_plan.json"
    config = {"run": str(run), "code": str(code), "script": "run_exp234_target_chunk.py",
              "arguments": [str(plan), "--plan-sha256", "abc"], "lease_id": "lease"}
    launch = {"config": config}
    exit_record = {"returncode": 0, "hard_timeout": False}
    status = {"status": "PASS_EXP234_TARGET_CHUNK_NO_LABELS"}
    (run / "launch.json").write_text(json.dumps(launch))
    (run / "exit.json").write_text(json.dumps(exit_record))
    state = {"monitor_status": "RELEASED_AFTER_VERIFIED_EXIT",
             "queue": {"state": "RELEASED", "id": "lease"},
             "exit": exit_record, "identity_alive": False, "group_alive": False,
             "gpu_pids": [], "status": status, "launch": launch}
    released(state, run, code, plan, "abc", status)
    for field, bad in (("monitor_status", "MONITORING"), ("group_alive", True),
                       ("gpu_pids", [123]), ("status", {"status": "INCOMPLETE"})):
        broken = {**state, field: bad}
        with pytest.raises(AssertionError):
            released(broken, run, code, plan, "abc", status)
