# Secondary full fold0 saved-release gate — local handoff

Prepared 2026-09-27 UTC for the already-running **attempt `07911298d0f9`**.
This is a separate read-only postrun verifier; the sealed secondary package
was not edited. Its plan SHA256 remains
`af4bbe339c3bb665152028db7861b09501e3ddc093e48406ee067bbb6974baf3`
and 20-file bundle manifest SHA256 remains
`49d49d16683505853cd950ae2b088fdc9ff7c21c380fe601d6652263da9b9cb2`.
The verifier also pins the existing reservation SHA256
`5bcd0d0e7ae7a2c3636b67b7f86a63024fb70aa4e11be9ed96f371cd8c076abc`,
launch intent SHA256
`cc0116596c669fb1ae1c8e0522daacdb5b653f583b44624e3352e36796e9d6ba`
and launch receipt SHA256
`15b12752a9f0ab4dbd89d44856ad2a101c0c0c9040b49ab1758eb06a5adb9ff8`.

## Run only after exit and lease release

From the repository root:

```powershell
python -B work/loeo-secondary-f0-release-gate-20260928/verify_release.py --check
```

Verifier source: `work/loeo-secondary-f0-release-gate-20260928/verify_release.py`,
SHA256 `e3f48cc6ebfee49a93fcbdf9a71a8f3718a38ffbff1e49d09a07771e83e441d3`.
It uses only read-only SSH to fetch the exact run's `config.json`,
`launch.json`, `exit.json`, `supervision/complete.json` and queue `status`.
Remote JSON bytes are rehashed locally; the saved `complete.json` SHA is
recorded. The expected run, lease and GPU come from the pinned local plan,
reservation and launch intent. The gate checks exit0/no timeout, child PID and
start identity, matching run/lease/GPU/exit, release-time no live process or
GPU PID, ordered observation/control/completion times, current queue
`RELEASED`, and the **saved raw release reply** with exact `id` and
`state=RELEASED`. A later tenant's current GPU activity does not invalidate
the saved release-time observation.

If remote supervisor completion is absent, an immutable local
`full_manual_release_receipt.json` may supply the release observation and
reply; its SHA is recorded. A present but false supervisor completion cannot
be overridden by a manual receipt. Missing exit, unreleased queue, missing
release evidence, incomplete JSON, or transient SSH yields `INCONCLUSIVE`
with **no final receipt**. Once all terminal evidence is present, the verifier
exclusively writes one immutable local
`work/loeo-secondary-f0-release-gate-20260928/secondary_f0_release_gate_final.json`
with `PASS` or `FAIL`; a second run cannot overwrite it. Both this gate and
the existing independent full-training audit must pass before considering
outer inference. Neither result is an OOF score.

## Local validation and boundary

`python -B work/loeo-secondary-f0-release-gate-20260928/test_verify_release.py`
passed **8/8** synthetic tests. Test source SHA256 is
`dc77755a35d46445786273e08c3087a971da9d164db8d5a766c2e328349498a4`.
Fixtures cover `{}`, wrong lease, wrong state and valid saved queue replies;
manual fallback, release-time GPU/process/timestamp/exit identity, remote
complete-byte rehash, absent files, transport failure and one-shot receipt
behavior. Both Python sources AST-parse. No remote command, queue operation,
training, target-label read, Kaggle action, live-package edit or
`EXPERIMENTS.md` edit was performed in this preparation.
