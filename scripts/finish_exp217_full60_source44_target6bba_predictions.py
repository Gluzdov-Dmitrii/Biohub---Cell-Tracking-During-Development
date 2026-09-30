"""Finish EXP217 target6bba paired predictions; no metrics and no POST."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from monitor_exp213_job import QUEUE, ssh

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
REPORT = LOCAL / "reports/exp217_full60_source44_target6bba_prediction_progress_20260915.json"
LANES = [["44b6_00", "44b6_02", "44b6_04"], ["44b6_01", "44b6_03"]]


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
    prepare = json.loads(
        (LOCAL / "reports/exp217_full60_source44_target6bba_prepare_20260915.json").read_text()
    )
    assert prepare["status"] == "PASS_EXP217_FULL60_SOURCE44_TARGET6BBA_PREPARED"
    claim_path = LOCAL / "reports/exp217_full60_source44_target6bba_prediction_claim_20260915.json"
    if claim_path.exists():
        claim = json.loads(claim_path.read_text())
        assert claim["lanes"] == LANES, "Existing EXP217 prediction claim uses different lanes"
    else:
        with claim_path.open("x") as stream:
            json.dump(
                {
                    "started": time.time(),
                    "lanes": LANES,
                    "scope": "Five EXP217 source44b6 target6bba paired shards only; no target metrics or POST",
                },
                stream,
                indent=2,
            )
            stream.write("\n")
    configurations = {}
    for lane in LANES:
        for tag in lane:
            path = LOCAL / f"reports/exp217_full60_source44_target6bba_{tag}_config_20260915.json"
            config = json.loads(path.read_text())
            assert config["experiment"] == "EXP217"
            assert config["code"] == REMOTE + "/code/exp214_inference_v8_20260914"
            assert "--reuse-manifest" not in config["arguments"]
            configurations[tag] = (path, config, hashlib.sha256(path.read_bytes()).hexdigest())
    deadline = datetime.datetime(2026, 9, 15, 22, 0, tzinfo=datetime.timezone.utc).timestamp()
    tags = [tag for lane in LANES for tag in lane]
    while time.time() < deadline:
        queue = cluster_json("nsu-quadro", "python3 " + QUEUE + " status")["requests"]
        active = [row for row in queue if row["state"] not in ("RELEASED", "CANCELLED")]
        source = """import json
from pathlib import Path
r=Path(ROOT);rows={}
for tag in TAGS:
 p=r/('runs/exp217_full60_source44_target6bba_'+tag+'_20260915')
 if not p.exists():continue
 row={'exists':True}
 for name,key in [('exit.json','exit'),('output/status.json','prediction')]:
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
                    if "exit" in row:
                        assert row["exit"]["returncode"] == 0 and not row["exit"]["hard_timeout"], tag
                        assert row["prediction"]["status"] == "PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS"
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
                "status": "PASS_ALL_EXP217_TARGET6BBA_PREDICTIONS_RELEASED",
                "shards": completed,
                "movies": 116,
                "target_metrics_read": False,
                "reused_target44b6_baseline_shards": True,
            }
            source = (
                "import json\n"
                "from pathlib import Path\n"
                f"p=Path({REMOTE + '/code/exp217_full60_source44_target6bba_inputs_20260915/predictions_complete.json'!r})\n"
                f"v={result!r}\n"
                "text=json.dumps(v,indent=2)+'\\n'\n"
                "assert not p.exists() or p.read_text()==text\n"
                "p.write_text(text)\n"
                "print(json.dumps(v))\n"
            )
            cluster_json("nsu-quadro", "python3 -", source)
            save("COMPLETE_EXP217_TARGET6BBA_PREDICTIONS", completed=completed, movies=116)
            return
        save("RUNNING_EXP217_TARGET6BBA_PREDICTIONS", completed=completed, waiting_or_running=waiting, launched=launched)
        time.sleep(45)
    raise TimeoutError("Finite inference deadline reached; existing jobs retain monitors")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save("STOPPED_NEEDS_RECONCILIATION", error=str(error))
        traceback.print_exc()
        raise
