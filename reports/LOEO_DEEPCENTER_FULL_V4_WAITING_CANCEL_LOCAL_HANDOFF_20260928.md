# DeepCenter reciprocal full v4 — local waiting-cancel handoff

Date: 2026-09-28. **Local only; not approved for remote stage.** This
successor implements the immutable preregistration
`LOEO_DEEPCENTER_FULL_V4_WAITING_CANCEL_PREREG_20260928.md` SHA256
`c2f448be60dbc4c59e52c39a5993755ccd4f6958e4316876cd18680dfe9f7f07`.
The rejected v3 handoff SHA256 is
`5bae247cf4996d6c30668513bf7f138496193f57d4ac6d6249c4915b1779c134`.
All v1, v2, and v3 packages remain sealed, unmodified, unstaged, and unrun.

## Distinct sealed packages

| Fold | Attempt | Plan SHA256 | Training manifest SHA256 | Control manifest SHA256 | Auditor SHA256 | Controller SHA256 |
|---|---|---|---|---|---|---|
| 0 | `9a02c64d8335` | `906ad7a0265cd6a9efddfc1e77c3ef6425d42f4ab5cb862f0b3c70c273062951` | `3a7db9f1fe0883335434e2340603c2935e3cf003ae10c18c3d720a62012f9fc4` | `3eb97c37125c43c6feb4aea9ae0bebee0a9cfd7825409c18d198890d205e5547` | `bf453de8242c1c9a7cdb6813e9ae18c98b37e20c0ea4642a9a41c44306835227` | `edc73c9934fc08f5ed016ed39a91fc0578d4cb037e859d1ddbc61971ceb55e27` |
| 1 | `00092a70fb32` | `956be59d492bbb5223273d95e5afdd8ea837a3a5df3454d0b6b6db50def23066` | `e99ff848dd9256010e149d030f1c0165df405cde37e6c5423b592debf3454402` | `6181b912d94815ea65d6a5b64d370e2d2dfe39b29b940fa3adcf6f8b8142738d` | `d08245efa4293a591db8b2231279af6d32de6fb524ed031c95946f696f90f249` | `2a32c045b8f457dee18aea7f29bb46b568c2a2f13c38ac19d38b32a6f56e2eac` |

Both controllers pin the shared `local_recovery.py` SHA256
`7a85fefb4846e6a3c5a5175dbd78140ae5c81476d67fa1d828da0d40dd5789b4`.
The files are under `work/loeo-deepcenter-full-f{0,1}-v4-20260928/`,
`work/loeo-deepcenter-full-f{0,1}-control-v4-20260928/`, and
`work/loeo-deepcenter-v4-local-build-20260928/`.

## Recovery change

The controller writes source-frame metadata, then a sealed launch intent,
then makes one queue request. A received queue response is saved as
`queue_request_reply.json` before action. A WAITING response enters the same
fresh queue reconciliation as a lost response. Both paths require exact
ID/project/run/owner/token/pool/count/CPU/RAM/disk/minutes, `gpus=[]`, and
`process=null`. They also require absent remote run directories and matching
workers. The exclusive `cancel_attempt_receipt.json` is synced before one
`cancel --id/--token`. The raw cancel reply is synced separately. Only exact
`id` plus `state=CANCELLED`, a fresh exact closed queue row with no GPU or
process, and a second remote absence probe produce
`CANCELLED_WAITING_CONFIRMED`. Transport, reply, row, or probe uncertainty
remains explicit; no request or cancel is retried. A WAITING-to-RESERVED race
uses the existing fresh GPU/process/remote-run absence check before one
verified release. The v3 source-frame and full frame/intent/reservation/launch
lineage audit remains; v4 additionally binds the saved request reply to the
reservation in the final auditor.

Scientific contract is unchanged: source-only folds 0/1 use 56/15 and
102/26 fit/inner movies, respectively, two epochs, seed 2026, strict BCE
selection and quality gate. No outer labels were accessed for this work.

## Local verification

- Fold 0: 39 control/recovery/lineage/waiting tests and 6 training tests pass.
- Fold 1: 42 control/recovery/lineage/waiting tests and 6 training tests pass.
- Shared explicit-split trainer: 3 tests pass.
- `work/loeo-deepcenter-v4-local-build-20260928/verify_local.py` passes full
  v1-v4 hash lineage, both manifest entry/path/hash readbacks, 16 Python AST
  parses per fold, and confirms no `__pycache__` or `.pyc` files.
- Synthetic tests reproduce v3's accepted-WAITING/lost-reply stranding and
  cover v4 received/lost response, exact identity, busy worker, wrong/lost
  cancel reply, no duplicate cancel, WAITING-to-RESERVED before and after
  cancel, safe release, and request-reply auditor binding.

No SSH, queue mutation, GPU work, outer target read, GEFF read, Kaggle action,
or EXPERIMENTS/current-state/x138 edit was performed. This handoff awaits
independent v4 review before any remote stage. Operational outcomes remain
unverified on the live queue; uncertain states intentionally require a human
to inspect the durable receipts and current queue state.
