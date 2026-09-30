"""Launch the EXP217 CPU scoring worker after staging source files."""
import json
from pathlib import Path

from monitor_exp213_job import ssh

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def main() -> None:
    source = (LOCAL / "scripts/finish_exp217_full60_source44_target6bba_scoring.py").read_text()
    compare = (LOCAL / "scripts/compare_exp217_full60_source44.py").read_text()
    compare_base = (LOCAL / "scripts/compare_exp214_results.py").read_text()
    remote = r'''
import json
import os
from pathlib import Path
import resource
import subprocess

root = Path(__EXP217_ROOT__)
inp = root / "code/exp217_full60_source44_target6bba_inputs_20260915"
run = root / "runs/exp217_full60_source44_target6bba_score175_20260915"
assert inp.exists(), "EXP217 inputs are not staged"
assert (inp / "manifest.json").exists(), "EXP217 manifest is not staged"
assert not run.exists(), "Existing scoring worker; reconcile before retry"
run.mkdir(parents=True)
(run / "tmp").mkdir()
(inp / "finish_exp217_full60_source44_target6bba_scoring.py").write_text(__EXP217_SOURCE__)
(inp / "compare_exp217_full60_source44.py").write_text(__EXP217_COMPARE__)
(inp / "compare_exp214_results.py").write_text(__EXP217_COMPARE_BASE__)

def limits():
    os.sched_setaffinity(0, set(range(8)))
    resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**3, 64 * 1024**3))

env = dict(
    os.environ,
    CUDA_VISIBLE_DEVICES="",
    OMP_NUM_THREADS="8",
    MKL_NUM_THREADS="8",
    OPENBLAS_NUM_THREADS="8",
    PYTHONDONTWRITEBYTECODE="1",
    TMPDIR=str(run / "tmp"),
)
script = inp / "finish_exp217_full60_source44_target6bba_scoring.py"
with (run / "worker.log").open("x") as log:
    process = subprocess.Popen(
        [str(root / "envs/prepost/py3.11-stdlib-v1/bin/python"), str(script)],
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        preexec_fn=limits,
        start_new_session=True,
    )
identity = Path("/proc/" + str(process.pid) + "/stat").read_text().split(") ")[1].split()[19]
receipt = {
    "pid": process.pid,
    "start": identity,
    "script": str(script),
    "run": str(run),
    "deadline_utc": "2026-09-16T06:00:00Z",
}
(run / "worker_launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
'''.replace("__EXP217_ROOT__", repr(REMOTE)).replace("__EXP217_SOURCE__", repr(source)).replace(
        "__EXP217_COMPARE__", repr(compare)
    ).replace("__EXP217_COMPARE_BASE__", repr(compare_base))
    result = ssh("nsu-quadro", "python3 -", remote)
    (LOCAL / "reports/exp217_full60_source44_target6bba_cpu_launch_20260915.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
