"""One-shot read-only reconciliation of the failed EXP227 chunk07 v2 run."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, probe, ssh


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
STAGE = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_stage_20260927.json"
LAUNCH = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_attempt00_20260927_result.json"
RECEIPT = ROOT / "reports/exp227_target6bba_chunk07_v2_failed_reconciliation_20260927.json"
SOURCE_SHA = "8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3"
STAGE_SHA = "498a4cf13537bfffa9a90f601e4f909838583e3f334fc1d8b458c55f33bb3d3e"
LAUNCH_SHA = "fc713034eb4b674c3dbf4ffbe17205b7852d0228c21426581e5bd7a78a94d4be"
MANIFEST_SHA = "a828a02ef88bd313a30da12aca8eb2a956337c3641c4dc2851e49e50a203fade"
PLAN_SHA = "583fdae80ed8145ceca92d2405e69a6093b26700acc8986540a5f0ace6afcbd2"
RUNNER_SHA = "9d4c257149168525847b31b56897ff5640211d20c06c8ce8dded2bc974e8ea1a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def remote_source(code, run):
    return '''import hashlib,json,pathlib
code=pathlib.Path(CODE);run=pathlib.Path(RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
read=lambda p:json.loads(p.read_text()) if p.exists() else None
log=run/'inference.log';output=run/'output';runner=code/'run_exp227_target_chunk.py'
lines=runner.read_text().splitlines()
graph_files=[str(p.relative_to(run)) for p in run.rglob('graph__*.csv')]
print(json.dumps({'code_exists':code.is_dir(),'run_exists':run.is_dir(),
 'run_files':sorted(p.name for p in run.iterdir()),
 'output_exists':output.exists(),'graph_files':graph_files,
 'exit':read(run/'exit.json'),'complete':read(run/'supervision/complete.json'),
 'control':read(run/'supervision/control.json'),
 'inference_log_sha256':sha(log),'inference_log':log.read_text(),
 'runner_sha256':sha(runner),'runner_identity_lines':lines[61:64],
 'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json')}))
'''.replace("CODE", repr(code)).replace("RUN", repr(run))


def reconcile() -> dict:
    assert not RECEIPT.exists(), "Failure receipt exists; do not overwrite"
    assert sha(SOURCE) == SOURCE_SHA and sha(STAGE) == STAGE_SHA and sha(LAUNCH) == LAUNCH_SHA
    stage = json.loads(STAGE.read_text())
    launch = json.loads(LAUNCH.read_text())
    config = launch["config"]
    assert stage["manifest_sha256"] == MANIFEST_SHA and stage["plan_sha256"] == PLAN_SHA
    assert launch["status"] == "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V2"
    assert launch["attempt"] == 0 and launch["stage_sha256"] == STAGE_SHA
    assert launch["lease"]["id"] == config["lease_id"] == stage["lease_id"]
    assert launch["lease"]["run_path"] == config["run"] == stage["run"]
    assert config["code"] == stage["code"] and config["token"] == stage["token"]
    assert launch["target_labels_read"] is False and launch["kaggle_post"] is False
    state = ssh("nsu-a100", "python3 -", remote_source(stage["code"], stage["run"]))
    observed = probe(config)
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    rows = [row for row in queue["requests"] if row["id"] == stage["lease_id"]]
    assert len(rows) == 1
    row = rows[0]
    assert state["code_exists"] and state["run_exists"]
    assert state["manifest_sha256"] == MANIFEST_SHA and state["plan_sha256"] == PLAN_SHA
    assert state["runner_sha256"] == RUNNER_SHA
    assert state["runner_identity_lines"] == [
        '    token = f"exp227_target6bba_chunk{plan[\'chunk_index\']:02d}_v1_20260927"',
        '    assert plan["code"].endswith("/code/" + token)',
        '    assert plan["output"].endswith("/runs/" + token + "/output")']
    assert state["exit"] == observed["exit"]
    assert state["exit"]["returncode"] == 1 and state["exit"]["hard_timeout"] is False
    assert state["complete"] == {"at": state["complete"]["at"],
                                 "exit": state["exit"],
                                 "status": "RELEASED_AFTER_VERIFIED_EXIT"}
    assert state["control"]["action"] == "release"
    assert state["control"]["queue"] == row
    assert row["state"] == "RELEASED" and row["gpus"] == []
    assert row["process"] == {key: observed["launch"][key] for key in ("pid", "start")}
    assert observed["identity_alive"] is False and observed["group_alive"] is False
    assert observed["gpu_pids"] == []
    assert state["output_exists"] is False and state["graph_files"] == []
    assert observed["status"] is None
    assert 'line 63, in validate_plan' in state["inference_log"]
    assert 'assert plan["code"].endswith("/code/" + token)' in state["inference_log"]
    assert state["inference_log"].endswith("AssertionError\n")
    assert all("graph__" not in name for name in state["run_files"])
    body = {"status": "RECONCILED_EXP227_CHUNK07_V2_FAILED_BEFORE_GRAPHS",
            "source_stopped_sha256": SOURCE_SHA,
            "stage_sha256": STAGE_SHA, "launch_sha256": LAUNCH_SHA,
            "identity": {key: stage[key] for key in ("code", "run", "lease_id", "token")},
            "remote": {key: value for key, value in state.items()
                       if key != "inference_log"},
            "log_tail": state["inference_log"][-1800:],
            "process": observed,
            "queue_row": row,
            "queue_snapshot_sha256": hashlib.sha256(json.dumps(
                queue, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "graph_count": 0, "target_labels_read": False,
            "target_score_computed": False, "kaggle_post": False}
    with RECEIPT.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(body, indent=2) + "\n")
    assert sha(SOURCE) == SOURCE_SHA and sha(STAGE) == STAGE_SHA and sha(LAUNCH) == LAUNCH_SHA
    return {"status": body["status"], "receipt_sha256": sha(RECEIPT),
            "log_sha256": state["inference_log_sha256"],
            "queue_snapshot_sha256": body["queue_snapshot_sha256"]}


if __name__ == "__main__":
    print(json.dumps(reconcile()))
