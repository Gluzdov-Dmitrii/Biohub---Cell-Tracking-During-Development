"""Finite CPU-only supervisor for one reviewed EXP209 reconstructed scorer.

The launcher sends this source as exact bytes to a sibling control path. This
script is not part of the immutable 14-file scorer bundle and never reads GEFF.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
NAME = "exp209_reconstructed_current_scorer_v1_20260927"
CODE = Path(f"{REMOTE}/code/{NAME}")
RUN = Path(f"{REMOTE}/runs/{NAME}")
CONTROL = Path(f"{REMOTE}/runs/.{NAME}.control")
PYTHON = Path(f"{REMOTE}/envs/current-organizer-py311-e13cf-v1/bin/python")
MANIFEST_SHA = "2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb"
CONFIG_SHA = "d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335"
SCORER_SHA = "72e24bc53128c1e35ffe7dc806c74ccf0ad36575b52c5d7753ee60e2b3771b79"
WALL_SECONDS = 8 * 60 * 60
MEMORY_BYTES = 32 * 1024**3
CPU_COUNT = 8


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, value: dict) -> None:
    require(path.parent.is_dir(), f"missing control directory: {path.parent}")
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def process_tick(pid: int) -> int:
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    return int(stat.rsplit(") ", 1)[1].split()[19])


def original_worker_absent(pid: int, tick: int) -> bool:
    stat = Path(f"/proc/{pid}/stat")
    if not stat.exists():
        return True
    raw = stat.read_text(encoding="utf-8")
    fields = raw.rsplit(") ", 1)[1].split()
    return fields[0] == "Z" or int(fields[19]) != tick


def child_limits(cpus: tuple[int, ...]) -> None:
    import resource
    os.sched_setaffinity(0, set(cpus))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))


def file_hash_or_none(path: Path) -> str | None:
    return sha(path) if path.is_file() else None


def supervise(launch_intent_sha: str) -> dict:
    require(CODE.parent == Path(REMOTE) / "code" and RUN.parent == Path(REMOTE) / "runs" and
            CONTROL.parent == RUN.parent and not RUN.exists(),
            "scorer code/run/control namespace mismatch or existing output")
    require(CODE.is_dir() and CONTROL.is_dir() and PYTHON.is_file() and
            os.access(PYTHON, os.X_OK), "scorer code, control or interpreter absent")
    require(sha(CODE / "bundle_manifest.json") == MANIFEST_SHA and
            sha(CODE / "config.json") == CONFIG_SHA and
            sha(CODE / "score_exp209_reconstructed_current_v1.py") == SCORER_SHA,
            "scorer source changed after launch intent")
    intent_path = CONTROL / "launch_intent.json"
    require(sha(intent_path) == launch_intent_sha,
            "supervisor launch intent SHA changed")
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    require(intent["status"] == "LAUNCH_INTENT_EXP209_SCORER_V1_CPU_ONLY" and
            intent["bundle_manifest_sha256"] == MANIFEST_SHA and
            intent["config_sha256"] == CONFIG_SHA and
            intent["labels_read"] is False and intent["gpu_used"] is False,
            "supervisor launch intent fields changed")
    available = sorted(os.sched_getaffinity(0))
    require(len(available) >= CPU_COUNT, "fewer than eight CPUs available")
    cpus = tuple(available[-CPU_COUNT:])
    launch = {"status": "WORKER_INTENT_EXP209_SCORER_V1_CPU_ONLY",
              "code_dir": str(CODE), "run_root": str(RUN),
              "python": str(PYTHON), "cpu_affinity": list(cpus),
              "memory_limit_bytes": MEMORY_BYTES, "wall_timeout_seconds": WALL_SECONDS,
              "launch_intent_sha256": launch_intent_sha,
              "labels_read_before_scorer_gate": False, "gpu_used": False}
    write_once(CONTROL / "worker_intent.json", launch)
    env = dict(os.environ)
    env.update({"CUDA_VISIBLE_DEVICES": "", "PYTHONDONTWRITEBYTECODE": "1",
                "OMP_NUM_THREADS": str(CPU_COUNT), "MKL_NUM_THREADS": str(CPU_COUNT),
                "OPENBLAS_NUM_THREADS": str(CPU_COUNT),
                "NUMEXPR_NUM_THREADS": str(CPU_COUNT),
                "NUMBA_NUM_THREADS": str(CPU_COUNT),
                "TMPDIR": str(CONTROL)})
    command = [str(PYTHON), str(CODE / "score_exp209_reconstructed_current_v1.py"),
               "--config", str(CODE / "config.json"),
               "--config-sha256", CONFIG_SHA,
               "--bundle-manifest-sha256", MANIFEST_SHA]
    started_at = time.monotonic()
    with (CONTROL / "worker.log").open("xb") as log:
        worker = subprocess.Popen(command, cwd=CODE, env=env, stdout=log,
                                  stderr=subprocess.STDOUT, start_new_session=True,
                                  preexec_fn=lambda: child_limits(cpus))
        tick = process_tick(worker.pid)
        write_once(CONTROL / "worker_started.json",
                   {"status": "STARTED_EXP209_SCORER_V1_CPU_ONLY", "pid": worker.pid,
                    "start_tick": tick, "cpu_affinity": list(cpus),
                    "memory_limit_bytes": MEMORY_BYTES,
                    "wall_timeout_seconds": WALL_SECONDS,
                    "bundle_manifest_sha256": MANIFEST_SHA,
                    "config_sha256": CONFIG_SHA})
        timed_out = False
        try:
            exit_code = worker.wait(timeout=WALL_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(worker.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                exit_code = worker.wait(timeout=30)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(worker.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    exit_code = worker.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    exit_code = worker.poll()
        log.flush()
        os.fsync(log.fileno())
    elapsed = time.monotonic() - started_at
    absent = original_worker_absent(worker.pid, tick)
    result_sha = file_hash_or_none(RUN / "result.json")
    historical_sha = file_hash_or_none(RUN / "historical_replay.json")
    gate_sha = file_hash_or_none(RUN / "no_metric_gate.json")
    status = ("TIMEOUT_EXP209_SCORER_V1" if timed_out else
              "EXIT0_EXP209_SCORER_V1" if exit_code == 0 and result_sha else
              "FAILED_EXP209_SCORER_V1")
    completion = {"status": status, "exit_code": exit_code,
                  "timed_out": timed_out, "worker_pid": worker.pid,
                  "worker_start_tick": tick, "worker_absent": absent,
                  "duration_seconds": elapsed,
                  "run_root": str(RUN), "bundle_manifest_sha256": MANIFEST_SHA,
                  "config_sha256": CONFIG_SHA,
                  "no_metric_gate_sha256": gate_sha,
                  "historical_replay_sha256": historical_sha,
                  "result_sha256": result_sha,
                  "gpu_used": False, "kaggle_post": False}
    write_once(CONTROL / "completion.json", completion)
    return completion


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-intent-sha256", required=True)
    args = parser.parse_args()
    result = supervise(args.launch_intent_sha256)
    print(json.dumps({"status": result["status"], "exit_code": result["exit_code"],
                      "timed_out": result["timed_out"]}), flush=True)


if __name__ == "__main__":
    main()
