# LOEO primary full fold1 v3 — queue identity local handoff

Prepared 2026-09-28 Asia/Novosibirsk. **LOCAL ONLY:** no SSH, queue request,
GPU, outer `44b6` image or GEFF read, Kaggle POST, or OOF score. The ongoing
primary fold0 lease was untouched. Independent review is required before any
remote stage.

## Preregistration and sealed identity

- Preregistration:
  `reports/LOEO_PRIMARY_FULL_F1_V3_QUEUE_IDENTITY_PREREG_20260928.md`, SHA256
  `b3d0b23a3ee2f55fb443a7cec7564efca5e3207a9df5b79c0d76a5a918bb3d24`.
- Local package: `work/loeo-primary-full-f1-v3-20260928/`.
- Plan `full_plan.json` SHA256
  `68dc688662379c7f64d015e866f19c118c6c33f9cc343a5a31112354cc23c976`.
- Exact 21-file bundle manifest `full_bundle/bundle_manifest.json` SHA256
  `84a9774602a1d3f44cd7a8e7160f24f6be2b9518ebc9c61d051718761d355c72`.
- Fresh attempt `ef89673cfdf9`; lease
  `loeo-primary-full-f1-v3-ef89673cfdf9`. Planned remote code and run stems
  are `loeo_primary_full_f1_v3_ef89673cfdf9`; neither remote path was created.
- Rejected v2 remains unchanged: plan SHA256
  `4dcbd79f8e07ebec92bba37d96547ff521aa3ba7424ae12f1d7c4903725cb5c5`,
  manifest SHA256
  `681ffa4a9e816177c4c11d34eb8de4613190fc39cd9fcd2509f1a57e2552ff21`,
  auditor SHA256
  `9295030aac97b8e281d18c76d0776013a7fb4fcd4d1d4042f36477439c8dd926`.
  Neither v1 nor v2 was remotely staged, reserved or launched.

## Corrections and source-only contract

The scientific runner and wrapper bytes are unchanged: SHA256
`2278ace9041d0c820683a639c3953b95c8453514165d9e1ab1b05708af547057`
and `d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`.
The pinned split SHA256 is
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`:
102 fit and 26 inner `6bba` movies, 71 excluded outer `44b6` movies,
9,949/2,443 exact windows, 50 epochs, seed `20260930` before trainer import,
no warm start, and the same checkpoint selection and fixed quality gate.
Published primary weights remain identity metadata only.

V3 checks a returned reservation's exact lease ID, project, run path, token,
owner, RESERVED state, CURRENT health, alias, GPU count, pool, CPU, RAM, disk
and minutes against the immutable request before either remote launch call.
The controller writes an exclusive, flushed and fsynced
`full_request_intent.json` before the queue request. Timeout, malformed JSON,
or a mismatched reply preserves the intent and raw response/error evidence,
then reconciles the exact planned ID from live queue status. The intent blocks
a second request. A missing, duplicate or foreign live row is explicitly
unresolved. An active matching lease is released without a run only after an
independent remote probe sees no run directory, no run-owned process, one
physically empty allocated GPU, and no GPU compute PID. A present run needs a
matching launch/exit PID and start identity plus stopped process/GPU evidence.
All release branches retain the raw reply and require exact `id` and
`state=RELEASED`; an ambiguous release acknowledgement stays unresolved.

The final auditor now validates the pre-request intent and pinned RESERVED
receipt before assessing completion. It also validates the live RELEASED
row's stable identity and resources, the remote runtime config, the launched
GPU and saved release evidence. The fair queue clears `gpus` on release; the
released row may therefore have `gpus=[]`. The GPU identity comes from the
pinned RESERVED receipt and saved release-time evidence, with any nonempty
released GPU list required to match that identity. This corrects the additional
cross-audit blocker. The 28 exact named audit checks, including
`remote_source_metadata_matches`, remain unchanged. A real PASS still requires
all 28 to be true.

Source SHA256s: contract
`606639c3fa16488aa2735e88ff3b8eb39134495f545c5d7fd1036c9a1b096ea8`,
controller `9ef49822f7f186a51a33f5da1a7956f6cd3b6bf8b65919578a60ab5640ba37af`,
supervisor `451209c3b7e71bde342b92bfdf8936a3c2dc20e1e3ee13831a2bf429ada74fea`,
independent auditor `b9913e9a211321177d28fa4a275abe70daa1d8d86d2e1783685f469345715e28`.

## Local validation

- `python -B .../build_full_bundle.py validate-inputs`: 128 source IDs,
  71 excluded outer IDs, 13 pinned support files.
- `python -B .../test_full_local.py`: **24/24 passed**. Isolated mocks reproduce
  v2's foreign-ID/run `LAUNCHED` result with two remote launch calls, and its
  accepted-request timeout followed by `NO_RESERVATION_RECEIPT`. V3 rejects
  foreign ID/run/project/token/owner, missing fields and resource mismatches;
  verifies exact positive launch, timeout recovery and safe unlaunched release;
  leaves missing/foreign queue rows, occupied GPU and lost release replies
  unresolved; rejects foreign reservation in its independent auditor; and
  accepts the real post-release `gpus=[]` row format. Existing release-reply,
  PID/start, split, window and seed tests remain. Test SHA256
  `c761c138ffb58d2cfcbc4c739265c392cf3c78ac308900f528163890c941137d`.
- Eight local Python sources compiled without bytecode. `full_control.read_plan()`
  plus `verify_bundle()` reread and hashed all 21 manifest entries; there are
  22 physical bundle files including the manifest and no cache files.

## Remaining gates

Root must obtain a separate independent review of the new queue identity,
timeout recovery and final-audit logic. Before any later remote stage or
launch, refresh live queue fairness, foreign waiters, existing Biohub leases,
physical A100 idle and exact remote byte readback. The x138 assembler still
pins the rejected auditor and needs a distinct successor version with this
new independently reviewed auditor SHA before real source emission. This
handoff grants no remote, outer-target, Kaggle or OOF action.
