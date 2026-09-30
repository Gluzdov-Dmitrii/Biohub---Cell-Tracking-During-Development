"""Finish EXP218 target6bba public short-track rescue predictions; no metrics."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from monitor_exp213_job import QUEUE, ssh
from prepare_exp218_short_track_rescue import OVERRIDES

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
REPORT = LOCAL / "reports/exp218_short_track_rescue_prediction_progress_20260915.json"
LANES = [["44b6_00", "44b6_02", "44b6_04"], ["44b6_01", "44b6_03"]]
REMOTE_CODE = REMOTE + "/code/exp218_short_track_rescue_v1_20260915"
REMOTE_INPUT = REMOTE + "/code/exp218_short_track_rescue_inputs_20260915"


def save(status: str, **values) -> None:
    result = {"status": status, "updated": time.time(), **values}
    temp = REPORT.with_suffix(".partial")
    temp.write_text(json.dumps(result, indent=2) + "\n")
    temp.replace(REPORT)
    print(json.dumps(result), flush=True)


def cluster_json(alias: str, command: str, source: str | None = None, attempts: int = 4):
    last_error = None
    for attempt in range(attempts):
        try:
            return ssh(alias, command, source)
        except RuntimeError as error:
            last_error = error
            if attempt + 1 == attempts:
                break
            time.sleep(5 * (attempt + 1))
    raise last_error


def main() -> None:
    prepare = json.loads((LOCAL / "reports/exp218_short_track_rescue_prepare_20260915.json").read_text())
    assert prepare["status"] == "PASS_EXP218_SHORT_TRACK_RESCUE_PREPARED"
    claim_path = LOCAL / "reports/exp218_short_track_rescue_prediction_claim_20260915.json"
    if claim_path.exists():
        claim = json.loads(claim_path.read_text())
        assert claim["lanes"] == LANES, "Existing EXP218 prediction claim uses different lanes"
    else:
        with claim_path.open("x") as stream:
            json.dump(
                {
                    "started": time.time(),
                    "lanes": LANES,
                    "scope": "Five EXP218 source44b6 target6bba public shards only; no target metrics or POST",
                    "overrides": OVERRIDES,
                },
                stream,
                indent=2,
            )
            stream.write("\n")
    configurations = {}
    for lane in LANES:
        for tag in lane:
            path = LOCAL / f"reports/exp218_short_track_rescue_{tag}_config_20260915.json"
            config = json.loads(path.read_text())
            assert config["experiment"] == "EXP218"
            assert config["code"] == REMOTE_CODE
            assert config["script"] == "run_exp214_public_fold.py"
            assert "--reuse-manifest" not in config["arguments"]
            for override in OVERRIDES:
                assert override in config["arguments"]
            configurations[tag] = (path, config, hashlib.sha256(path.read_bytes()).hexdigest())
    deadline = datetime.datetime(2026, 9, 16, 4, 0, tzinfo=datetime.timezone.utc).timestamp()
    tags = [tag for lane in LANES for tag in lane]
    while time.time() < deadline:
        queue = cluster_json("nsu-quadro", "python3 " + QUEUE + " status")["requests"]
        active = [row for row in queue if row["state"] not in ("RELEASED", "CANCELLED")]
        source = """import json
from pathlib import Path
r=Path(ROOT);rows={}
for tag in TAGS:
 p=r/('runs/exp218_short_track_rescue_'+tag+'_20260915')
 if not p.exists():continue
 row={'exists':True}
 for name,key in [('exit.json','exit'),('output/inference_receipt.json','prediction')]:
  f=p/name
  if f.exists():row[key]=json.loads(f.read_text())
 rows[tag]=row
print(json.dumps(rows))
""".replace("ROOT", repr(REMOTE)).replace("TAGS", repr(tags))
        rows = cluster_json("nsu-quadro", "python3 -", source)
        completed, waiting, launched = [], [], []
        for lane in LANES:
            for tag in lane:
                path, config, digest = configurations[tag]
                assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, "Frozen inference config changed"
                row = rows.get(tag)
                if row:
                    if "exit" in row and "prediction" in row:
                        assert row["exit"]["returncode"] == 0 and not row["exit"]["hard_timeout"], tag
                        assert row["prediction"]["status"] == "PASS_FROZEN_PUBLIC_FAMILY_INFERENCE"
                        assert row["prediction"]["target_labels_read"] is False
                        assert row["prediction"].get("override_env") == dict(item.split("=", 1) for item in OVERRIDES)
                        monitor_path = Path(str(path).replace("_config_", "_monitor_"))
                        monitor = json.loads(monitor_path.read_text()) if monitor_path.exists() else {}
                        if monitor.get("monitor_status") == "RELEASED_AFTER_VERIFIED_EXIT":
                            assert monitor["queue"]["id"] == config["lease_id"]
                            assert monitor["queue"]["state"] == "RELEASED"
                            completed.append(tag)
                            continue
                    waiting.append(tag)
                    break
                own = [
                    item
                    for item in active
                    if item["project"] == "biohub-cell-tracking-during-development"
                    and item["state"] in ("RUNNING", "RESERVED")
                ]
                others = [
                    item
                    for item in active
                    if item["project"] != "biohub-cell-tracking-during-development"
                    and item["state"].startswith("WAITING")
                ]
                if len(own) >= 2 or (own and others):
                    waiting.append(tag)
                    break
                process = subprocess.run(
                    [
                        sys.executable,
                        "scripts/launch_exp214_job.py",
                        "--config",
                        str(path.relative_to(LOCAL)),
                        "--mode",
                        "inference",
                    ],
                    cwd=LOCAL,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                log = path.with_name(path.stem + "_finite_launch.log")
                log.write_text(process.stdout + "\n" + process.stderr)
                if process.returncode:
                    raise RuntimeError("Launch stopped; reconcile any reserved lease: " + str(log))
                active.append(json.loads(process.stdout)["lease"])
                launched.append(tag)
                break
        if len(completed) == 5:
            result = {
                "status": "PASS_ALL_EXP218_SHORT_TRACK_RESCUE_PREDICTIONS_RELEASED",
                "shards": completed,
                "movies": 116,
                "target_metrics_read": False,
                "reused_target44b6_baseline_shards": True,
                "overrides": OVERRIDES,
            }
            source = (
                "import json\n"
                "from pathlib import Path\n"
                f"p=Path({REMOTE_INPUT + '/predictions_complete.json'!r})\n"
                f"v={result!r}\n"
                "text=json.dumps(v,indent=2)+'\\n'\n"
                "assert not p.exists() or p.read_text()==text\n"
                "p.write_text(text)\n"
                "print(json.dumps(v))\n"
            )
            cluster_json("nsu-quadro", "python3 -", source)
            save("COMPLETE_EXP218_SHORT_TRACK_RESCUE_PREDICTIONS", completed=completed, movies=116)
            return
        save("RUNNING_EXP218_SHORT_TRACK_RESCUE_PREDICTIONS", completed=completed, waiting_or_running=waiting, launched=launched)
        time.sleep(45)
    raise TimeoutError("Finite inference deadline reached; existing jobs retain monitors")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save("STOPPED_NEEDS_RECONCILIATION", error=str(error))
        traceback.print_exc()
        raise
