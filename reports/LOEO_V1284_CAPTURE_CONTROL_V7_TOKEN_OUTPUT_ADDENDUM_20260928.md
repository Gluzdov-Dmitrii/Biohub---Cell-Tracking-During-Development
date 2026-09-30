# Control-v7 preregistration addendum — terminal output and protocol label

Written 2026-09-28 before changing the control-v7 CLI and runtime completion.
The control-v7 terminal-row correction preregistration is
`reports/LOEO_V1284_CAPTURE_CONTROL_V7_TERMINAL_QUEUE_IDENTITY_PREREG_20260928.md`
SHA256 `157bd58e04351196c7f488e7fdc70d8673c0f7b89aaf3b85764a51da553ab38a`.
The sealed source-v5/control-v6 packages remain unchanged and blocked from
remote staging pending this successor's independent review.

The inherited `reconcile` CLI prints its entire returned dictionary. That
dictionary may contain live `queue_row` or `fresh_row` objects with the
private lease token. Control-v7 must preserve complete raw queue replies and
reconciliation JSON files for durable audit, but print only a fixed safe
summary: status, lease ID and plan SHA256. No error payload, queue row, token,
raw stdout/stderr or nested object may appear on stdout. Add a CLI test that
injects a token-bearing reconciliation result and proves absence of the token
and row from stdout while the returned/receipted object remains unchanged.

The source-v5 verifier is sealed and accepts the literal outcome
`PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6`. For control-v7 this string is
a compatibility protocol label, not the implementation version. Keep that
literal solely for the sealed verifier, and add explicit
`runtime_audit.control_release = "v7"` plus the exact
`runtime_audit.control_manifest_sha256` to each successful independent
completion. Local tests and the future head audit must require all three;
the actual controller identity is v7. If a later source verifier is revised,
it can adopt a new outcome literal through a distinct source package.

No remote stage, queue/GPU action, target-label/outer-GEFF read, Kaggle POST,
EXPERIMENTS.md edit or current-state report edit is authorized here.
