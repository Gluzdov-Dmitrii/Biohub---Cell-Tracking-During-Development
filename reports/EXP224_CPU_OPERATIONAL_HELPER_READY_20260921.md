# EXP224 CPU launcher ready; no job started

No staging or launch was performed. Scientific implementation remains the
Grok-authored `scripts/run_exp224_fixed_nodes.py`, pending parent review/tests.

Operational files:
- `scripts/stage_launch_exp224_cpu.py --config <final.json>` stages only.
- Add `--launch` only after parent approves the reviewed code/config.
- `scripts/exp224_cpu_wrapper.py` is the remote finite worker supervisor.
- Template: `reports/exp224_cpu_launch_config_template_20260921.json`.

Parent must fill exact CLI arguments and explicit dependency/config files,
set reviewed_sources to the SHA256 of every payload file, and set
launch_approved_after_code_review=true. Missing or mismatched reviewed hashes
block launch. Arguments support `{code}`, `{run}`, `{root}` substitutions and
are passed as an argv list, never shell commands. Code and inputs are immutable
after staging; revised payloads use a new experiment-owned code version.

The verified source8 input package is mandatory. Staging verifies remote
baseline CSV, inference receipt, metric artifact and source manifest hashes.
It reads the common queue on canonical prepost and checks actual free RAM,
load, disk and aggregate registered allocations. Following EXP220 policy,
CPU-only work does not obtain a fictitious GPU lease.

Execution is detached and fully remote on prepost,4CPU threads,32GiB address
space limit, CUDA hidden,7200s timeout, TERM then30s grace then KILL of only
the owned process group. Remaining owned group children are cleaned on normal
exit. `wrapper_launch.json`, `launch.json`, `worker.log`, `exit.json` retain
PID/start identity, exact command/config, returncode/timeout and cleanup facts.
Existing run directory blocks duplicate launch.

Validation: all helper files compile; overbudget CPU config rejection passes.
No training/scoring jobs were used to test this operational preparation.
