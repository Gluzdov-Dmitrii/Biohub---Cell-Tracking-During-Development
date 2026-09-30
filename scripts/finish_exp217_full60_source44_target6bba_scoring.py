"""Finite CPU-only EXP217 full175 score after all target6bba predictions release."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path("/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development")
RUN = ROOT / "runs/exp217_full60_source44_target6bba_score175_20260915"
CODE = ROOT / "code/exp214_inference_v8_20260914"
INPUT = ROOT / "code/exp217_full60_source44_target6bba_inputs_20260915"


def save(status: str, **values) -> None:
    result = {"status": status, "updated": time.time(), **values}
    temp = RUN / "status.partial"
    temp.write_text(json.dumps(result, indent=2) + "\n")
    temp.replace(RUN / "status.json")


def main() -> None:
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    deadline = datetime.datetime(2026, 9, 16, 6, 0, tzinfo=datetime.timezone.utc).timestamp()
    marker = INPUT / "predictions_complete.json"
    while not marker.exists() and time.time() < deadline:
        save("WAITING_EXP217_TARGET6BBA_PREDICTIONS")
        time.sleep(45)
    assert marker.exists(), "Finite readiness deadline reached"
    ready = json.loads(marker.read_text())
    assert ready["status"] == "PASS_ALL_EXP217_TARGET6BBA_PREDICTIONS_RELEASED"
    assert ready["movies"] == 116 and len(ready["shards"]) == 5
    out = RUN / "output"
    commands = [
        [
            CODE / "score_exp214_paired.py",
            "--repo",
            ROOT / "code/exp214_honest_refit_v4_20260912/tracking_repo",
            "--data",
            ROOT / "data/exp213_source_view_20260912",
            "--manifest",
            INPUT / "manifest.json",
            "--output",
            out / "full175",
        ],
        [
            INPUT / "compare_exp217_full60_source44.py",
            "--metrics",
            out / "full175/metrics.json",
            "--output",
            out / "comparison.json",
        ],
    ]
    for index, arguments in enumerate(commands):
        timeout = min(5400, int(deadline - time.time()))
        assert timeout > 0
        save("SCORING_EXP217_FULL60_SOURCE44_COMPARISON", step=index)
        command = [sys.executable, *map(str, arguments)]
        with (RUN / f"step{index}.log").open("x") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = Path(f"/proc/{process.pid}/stat").read_text().split(") ")[1].split()[19]
            (RUN / f"step{index}_launch.json").write_text(
                json.dumps({"pid": process.pid, "start": identity, "command": command, "started": time.time()}, indent=2)
                + "\n"
            )
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise
        (RUN / f"step{index}_exit.json").write_text(json.dumps({"returncode": code, "finished": time.time()}, indent=2) + "\n")
        assert code == 0, f"Score step{index} failed; no automatic retry"
    save("COMPLETE_EXP217_FULL60_SOURCE44_PAIRED175_COMPARISON")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save("STOPPED_NO_AUTOMATIC_RETRY", error=str(error))
        raise
