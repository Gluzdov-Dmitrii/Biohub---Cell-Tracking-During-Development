# LOEO secondary full fold1 v4 — local waiting cancellation handoff

Prepared 2026-09-28, local only. Correction preregistration
`reports/LOEO_SECONDARY_FULL_F1_V4_WAITING_CANCEL_PREREG_20260928.md`
SHA256 `3eb50af73b46448ec9be5d2a0715fbbf4f79aa06cd29b1ac5ce7ae0d567706b8`
preceded implementation. The earlier static PASS for v3 was retracted.
Rejected v3 is unchanged and unlaunched: plan SHA256
`9c1061c4d9e524aa572181834711c5414c07d7ff16f6aecd7af99ccfd8dc28d0`,
21-file manifest SHA256 `07a957514e58047f81ec623a42437b39e25b899707238873b03a5c2eac063113`,
auditor SHA256 `52285517ac376e0183d13d61190de5d12c9d606a19664b93749741e421c2fcb9`.
V1 and v2 remain rejected and unlaunched too.

## New v4 seal

- Package: `work/loeo-secondary-full-f1-v4-20260928/`.
- Attempt `95fcfa680631`; lease `loeo-secondary-full-f1-v4-95fcfa680631`.
- Plan `full_plan.json` SHA256 `5c275b92e5619b017d8143cc41052fe9f4eb9093f61b917b409e68a8a7b3892b`.
- Exact 21-file bundle manifest SHA256
  `7a2aacb0348a59fd5a68341efe333b25db2831b9b888728791df352a5bbf1869`.
- Contract SHA256 `ff65d70c4eb942431cb60e79b3b2ffd6086acab9d6f7d9f19fa155c12c6b92d0`;
  supervisor `451209c3b7e71bde342b92bfdf8936a3c2dc20e1e3ee13831a2bf429ada74fea`;
  controller `773d3fadf333d2f42745ffde6d680ed5ba69327fd04a1db7666e1826b87bcf83`;
  independent auditor `52285517ac376e0183d13d61190de5d12c9d606a19664b93749741e421c2fcb9`.
- Builder SHA256 `eed88e0b8f3e912a20e7a963ef087052966589156ab2f2d6150e34c83f850557`;
  local tests SHA256 `8c5e39176b381f1018c6cd1cf57e53f9597eb4c3b5c6d0007ed049b6dd1035e7`.
- Proposed remote code/run stem is `loeo_secondary_full_f1_v4_95fcfa680631`
  under the pinned Biohub project roots. Neither remote path was created.

The fold1 scientific split remains SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`:
102 fit and 26 inner `6bba` source movies, all 71 `44b6` outer movies excluded,
9,949/2,443 exact windows, 50 epochs, seed `20260929` before model import,
no warm start, unchanged trainer/model/augmentation, latest-tie source-inner
selection and 0.80/0.80/0.97 quality thresholds. Runner SHA256
`d59da08bceade68c7b8125c051be42faffe651e6add4f6cb6b777268e30f891c`
and wrapper SHA256 `d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`
are byte-identical to v3. Source window metadata SHA256 remains
`584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`.

## Waiting and cancellation correction

The controller now receives the raw queue request reply itself; a complete
`WAITING_RESOURCE` reply cannot trigger the old helper's unreceipted cancel.
After a lost or incomplete reply, the exclusive, fsynced request intent
prevents a duplicate request. A live waiting row must match this lease's
ID, project, run, owner, token, pool, quantities, `gpus=[]`, no process and
`state=WAITING_RESOURCE`. The controller verifies no run directory or run-owned
process, rereads the queue, then writes an exclusive, fsynced cancel intent
before one exact `cancel --id/--token`. It saves the raw cancel reply and
requires exact `id`/`state=CANCELLED`, a fresh matching cancelled row with
empty GPU/process, and another absent-run probe before claiming cancellation.
Ambiguous replies preserve evidence without repeating cancel.

If waiting becomes `RESERVED` before cancel, or cancel rejects it after that
transition, the controller reroutes to v3's no-run/no-process/empty-GPU
unlaunched release proof. It never cancels an active lease. The v3 released
queue semantics (`gpus=[]`) and all 28 exact named final-audit checks remain.

## Validation and remaining gates

`python -B work/loeo-secondary-full-f1-v4-20260928/test_full_local.py`
passed **30/30** tests, including complete and lost waiting replies, exact
cancel success, malformed raw reply, lost cancel response without retry,
WAITING→RESERVED before and during cancel, wrong waiting identity and an
active-looking cancelled row. The inherited v3 reservation/release, PID/start,
source/window/seed tests passed. `validate-inputs` found 128 source IDs, 71
sealed outer IDs and 13 support files. Final `read_plan()` and
`verify_bundle()` passed exact 21-file/hash readback; no-cache compilation
passed for 27 local/bundled Python files. The final auditor has the same 28
named checks as v3.

An independent read-only second review is required before remote stage.
The active primary fold0 lease was untouched. No SSH, queue request, GPU,
outer image/GEFF read, Kaggle POST, source emission or OOF claim occurred.
The x138 assembler pins must be updated separately after v4 review.
