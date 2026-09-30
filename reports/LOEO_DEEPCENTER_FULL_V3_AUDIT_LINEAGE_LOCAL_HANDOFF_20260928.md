# DeepCenter reciprocal full v3 audit-lineage local handoff — 2026-09-28

## Identity and scope

This local-only successor implements
`reports/LOEO_DEEPCENTER_FULL_V3_AUDIT_LINEAGE_PREREG_20260928.md`
SHA256 `444ab6eee1eea110bb13e145dd354663b79925585412cd20fdefe799b0c8ef0d`.
The rejected v2 packages and all v1 seals remain unchanged and unrun. New
attempts are fold 0 `43415dc5570a` and fold 1 `6aa9b5ee1d28`; their lease,
code and run paths contain `v3` and the corresponding new attempt.

| Fold | Plan SHA256 | Training manifest SHA256 | Remote control manifest SHA256 | Auditor SHA256 |
| --- | --- | --- | --- | --- |
| 0, source `44b6`, 56 fit/15 inner | `2acdcf24ed64cedd6a341d2b93df93881d69399d652f0209fb26eb90e4ef3d61` | `e8cff3b24a289cd1f3197f15d98c3e23e7febb54966bf9b0d129317e201fea0c` | `a4ea025380a8e8c4d4e83a97f61142f1291760f629e0d7d72dd952940adf0f78` | `ee1ad9ef9dd97d8f6643f1f7d822f840643df5c20a027b1133a3e2c22b6b3ca3` |
| 1, source `6bba`, 102 fit/26 inner | `93169574cd9b62070403ef3d5bdbab47e2c357b5f3009b8f4fdd60b4825b5428` | `704e1e7867e407581e4c66ac82f5455c8fc6f124ea055a5d607faec814e3585b` | `d78a86d56d098d59d56ef916c548f9724f33c3dc686c7205b58ca632bafc3b82` | `bf5438a9aecc014db6ba878c416d4d5d1184322f8bea47b57de7381130a69614` |

Training directories are `work/loeo-deepcenter-full-f0-v3-20260928` and
`work/loeo-deepcenter-full-f1-v3-20260928`; each has a corresponding
`-control-v3-20260928` directory. The controller SHAs are fold 0
`04b0a4c6c6f6c94d224e64e5727895e34c74863ec784d33a95e5dda48e026bdd`
and fold 1 `90e97a318834992d56bc30f2226f33e59fc717736660665dbcd6818e4ab96a6b`.
The unchanged v2 recovery source SHA256 is
`6b71159139873242a33b5f42d05fc44e3e6edcd4762d3ace9048f03e869deb0e`.

## Audit correction

Both independent auditors now hash the bytes actually read from
`launch_intent.json` and require that SHA256 in `launch_receipt.intent_sha256`.
The lineage gate checks intent plan/training/control/controller hashes,
lease ID, project, run/control paths, hard cap and token against the immutable
plan and reservation. It checks the queue lease identity, reservation plan,
launch plan and exact saved lease. It requires finite numeric timestamps in
the order `frame.at <= intent.at <= reservation.at <= launch.at`, rejecting
booleans, NaN, infinity, missing and out-of-order values. The v2 per-ID
source frame, link-target, split/root, batch, and remote-verifier comparisons
remain. Individual lineage flags are included in the final audit receipt;
the existing `pre_reservation_frames_bound` check passes only if every flag
passes. The launch receipt check also independently binds the actual intent
hash.

The scientific source-only experiment is unchanged: split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`,
trainer SHA256 `6314efc742acbf67e3fce66033f1e3736a9d0f88de72ebe630b7bba12d5f7425`,
two epochs, seed 2026, cold start, strict source-inner BCE selection and the
same fixed quality gate. The v2 pre-request frame measurement and guarded
ambiguous-request/one-shot release paths were copied unchanged.

## Local validation and remaining gate

- Fold 0: six training tests and 28 control/recovery/lineage tests passed.
  Fold 1: six training tests and 31 control/recovery/lineage tests passed.
  Three unchanged explicit-trainer tests passed.
- Seven new lineage tests per fold evaluate the exact v2 auditor AST predicate
  against its real v2 plan and synthetic malformed evidence: wrong intent
  fields, wrong launch intent hash, and a frame receipt after reservation
  still satisfy that v2 predicate. The v3 gate rejects each and passes a
  fully bound chain. Missing, nonfinite, wrong reservation/launch and malformed
  frame evidence also fail v3.
- Both nine-file training bundles passed `verify_bundle.py`. Read-only
  `work/loeo-deepcenter-v3-local-build-20260928/verify_local.py` rehashed all
  v1/v2 sealed plans and manifests, all v3 manifest file sets/sizes/SHAs,
  unchanged trainer and split, and parsed 15 Python sources per fold in
  memory with no bytecode caches. Synthetic tests also AST-parse generated
  transport scripts without executing them.

No SSH, remote stage, queue request/release, GPU work, outer image/GEFF read,
Kaggle action, `EXPERIMENTS.md`, current-state report or x138 edit occurred.
Remote Linux behavior and actual fold-0 frame totals remain unverified.
Independent second review of these exact v3 hashes is required before any
stage. Later x138 assembler auditor SHA pins need a distinct version.
