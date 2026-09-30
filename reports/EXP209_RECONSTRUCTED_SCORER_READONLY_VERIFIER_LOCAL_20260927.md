# EXP209 reconstructed scorer v1 — independent read-only verifier handoff

Status: **PREPARED_PENDING_SCORER_COMPLETION**, 2026-09-27. A single read-only
status probe found the existing launched worker's completion receipt absent
and its scorer output path absent. No score is claimed. Per root direction,
the verifier was prepared and was **not** invoked against the long live run.

Verifier: `scripts/verify_exp209_reconstructed_scorer_v1.py`, SHA256
`ed690e9b3bf96e8da3ab9529ec1785f18bf3e0ad9fa3dd18ef9e7771f2b3654e`.
Tests: `tests/test_verify_exp209_reconstructed_scorer_v1.py`, SHA256
`6e447222336122452aa7eab0141de57f810f29699a1833c065c2b71ff91bde56`.
Four synthetic tests and local/remote-source compilation passed. Tests cover
all175 historical row and pooled projection comparison, tampering, exact local
stage/launch receipt SHA pins, nonfinite receipt rejection, and pending/failed
worker states producing no score. They did not contact SSH, open GEFF, or run
either metric.

The verifier pins the actual local stage receipt SHA256
`1b386b7d454faec04344c93233fd5c01e479953214482671766c8a3ee9e36369`
and launch receipt SHA256
`8f09dd93bca396879f30f205cced07e3a1516631f25241e29d82fdf518167566`.
After supervisor completion it reads, without mutation, the remote staged
15-file scorer bundle and config, stage/launch intents and exact hash readback,
supervisor and worker identities/exit/no-timeout/absence, both logs, the pinned
reconstruction contract and gate, and the scorer's three expected output JSON
files. It rehashes all175 actual graph CSV and receipt bytes against the
no-metric gate, compares all175 historical EXP209 rows and the pooled
projection to archived values at absolute tolerance 1e-12, checks the current
organizer's exact metric/division/tracksdata pins, 175 unique ordered finite
rows and summary, output hash links, and absence of anomaly files. It never
opens GEFF or executes a metric. Original EXP209 graph byte identity remains
unavailable; a verified score is a leakage-controlled reciprocal
new-reconstruction estimate with historically exposed labels.

After real completion, root can invoke from the workspace root:

```powershell
python scripts/verify_exp209_reconstructed_scorer_v1.py
```

RUNNING, SETTLING and FAILED states print compact status and write no pass
receipt. Only full PASS writes the exclusive local
`reports/exp209_reconstructed_scorer_v1_readonly_verify_20260927.json`, with
the historical/current scores and exact output hashes. The verifier does not
stage, launch, restart, read labels, use GPU, or POST to Kaggle.
