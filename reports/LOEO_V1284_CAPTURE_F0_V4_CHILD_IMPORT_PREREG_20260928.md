# V1284 fold0 capture v4 — predictor child import-path correction

Written 2026-09-28 before editing the v4 cell builder or canary. Earlier v4
preregistrations and the failed v3 run remain unchanged.

The v3 wrapper starts `run_capture.py` with `PYTHONPATH` set to the sealed
capture code directory, but executed cell4 overwrites the predictor child's
environment with `PYTHONPATH=src`. The child runs from the materialized
support repository. Its patched predictor imports `capture_guard` from the
sealed code directory, which the materializer does not copy into that
repository. Thus the first predictor child would raise `ModuleNotFoundError`
after the LF hash gate is repaired.

In v4 cell4, build the predictor child's path from the repository's `src`
directory **and** the absolute sealed capture-code directory obtained from
the imported `capture_contract.HERE`. Apply the same path to both one-GPU
`subprocess.run` and sharded `subprocess.Popen` branches, preserving their
other environment values. The CPU canary shall capture that exact mocked
child environment and execute a real, CPU-only subprocess from the mock
repository with the same cwd/env, importing both `capture_guard` and
`biohub_tracking`. Run it for LF and CRLF parent predictor inputs. This test
must fail under the old `PYTHONPATH=src` behavior. Update executable-cell
hashes, package manifest and control source pin, and require independent
review before remote stage or GPU. No target GEFF, training or scoring.
