"""Bounded CPU-only EXP209 reconstruction supervisor; new run namespace only."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

from run_exp209_reconstruction_chunk_v1 import check_contract, forbid_labels, require, sha256


RAM_LIMIT = 16 * (1 << 30)
PREFLIGHT_TIMEOUT_SECONDS = 3600
CHUNK_TIMEOUT_SECONDS = 3600


def write_once(path: Path, payload: dict) -> None:
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def start_tick(pid: int) -> int:
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    return int(stat.rsplit(") ", 1)[1].split()[19])


def original_worker_absent(pid: int, tick: int) -> bool:
    try:
        return start_tick(pid) != tick
    except FileNotFoundError:
        return True


def limit_resources() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (RAM_LIMIT, RAM_LIMIT))


def worker(command: list[str], log: Path, timeout: int) -> dict:
    env = dict(os.environ)
    env.update({"CUDA_VISIBLE_DEVICES": "", "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "8", "MKL_NUM_THREADS": "8"})
    with log.open("x", encoding="utf-8") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                   env=env, preexec_fn=limit_resources)
        pid = process.pid
        tick = start_tick(pid)
        timed_out = False
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            exit_code = process.wait(timeout=30)
    return {"worker_pid": pid, "worker_start_tick": tick,
            "exit_code": exit_code, "timed_out": timed_out,
            "worker_absent": original_worker_absent(pid, tick)}


def supervise(contract_path: Path, run_root: Path) -> None:
    forbid_labels()
    require(os.environ.get("CUDA_VISIBLE_DEVICES", "") in {"", "-1"}, "CUDA must be hidden")
    contract, _historical, _manifest = check_contract(contract_path)
    require(run_root == Path(contract["run_root"]) and run_root.is_dir(), "run root mismatch/missing")
    require((run_root / "launch_intent.json").is_file(), "one-shot launch intent missing")
    require(json.loads((run_root / "launch_intent.json").read_text())["contract_sha256"] == sha256(contract_path),
            "launch intent contract changed")
    require(not (run_root / "preflight.json").exists(), "preflight already exists")
    code_dir = Path(contract["code_dir"])
    preflight = worker([sys.executable, str(code_dir / "preflight_exp209_reconstruction_v1.py"),
                        "--contract", str(contract_path), "--output", str(run_root / "preflight.json")],
                       run_root / "preflight.log", PREFLIGHT_TIMEOUT_SECONDS)
    write_once(run_root / "preflight_completion.json",
               {"status": "EXIT0" if preflight["exit_code"] == 0 and not preflight["timed_out"] else "STOPPED",
                **preflight})
    require(preflight["exit_code"] == 0 and not preflight["timed_out"] and preflight["worker_absent"],
            "full175 preflight failed; no graph work allowed")
    chunks_root = run_root / "chunks"
    chunks_root.mkdir(exist_ok=False)
    for chunk in contract["chunks"]:
        name = chunk["name"]
        directory = chunks_root / name
        directory.mkdir(exist_ok=False)
        outcome = worker([sys.executable, str(code_dir / "run_exp209_reconstruction_chunk_v1.py"),
                          "--contract", str(contract_path), "--chunk", name,
                          "--output", str(directory / "output")],
                         directory / "worker.log", CHUNK_TIMEOUT_SECONDS)
        complete = outcome["exit_code"] == 0 and not outcome["timed_out"] and outcome["worker_absent"]
        write_once(directory / "completion.json",
                   {"status": "EXIT0" if complete else "STOPPED", "chunk": name, **outcome})
        write_once(directory / "release.json",
                   {"status": "RELEASED" if outcome["worker_absent"] else "NOT_RELEASED",
                    "chunk": name, "worker_pid": outcome["worker_pid"],
                    "worker_start_tick": outcome["worker_start_tick"],
                    "worker_absent": outcome["worker_absent"]})
        require(complete, f"chunk failed or worker remains live: {name}")
        status = json.loads((directory / "output" / "status.json").read_text(encoding="utf-8"))
        require(status["status"] == "PASS_EXP209_RECONSTRUCTION_CHUNK_NO_LABELS" and
                status["chunk"] == name, f"chunk status mismatch: {name}")
    write_once(run_root / "supervisor_complete.json",
               {"status": "ALL_EIGHT_CHUNKS_EXIT0_RELEASED_NO_LABELS",
                "contract_sha256": sha256(contract_path), "movie_count": 175,
                "labels_read": False, "gpu_used": False})
    verification = worker([sys.executable, str(code_dir / "verify_exp209_reconstruction_graphs_v1.py"),
                           "--contract", str(contract_path), "--run-root", str(run_root),
                           "--output", str(run_root / "no_metric_gate.json")],
                          run_root / "verifier.log", 1800)
    verified = (verification["exit_code"] == 0 and not verification["timed_out"]
                and verification["worker_absent"] and (run_root / "no_metric_gate.json").is_file())
    write_once(run_root / "verifier_completion.json",
               {"status": "EXIT0" if verified else "STOPPED", **verification,
                "no_metric_gate_sha256": sha256(run_root / "no_metric_gate.json") if verified else None})
    require(verified, "postrun full175 no-label graph verifier failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    supervise(args.contract, args.run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
