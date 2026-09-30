# DeepCenter reciprocal full v3 — frame and launch lineage audit

Written 2026-09-28 before successor implementation. Independent read-only
review **rejected both local DeepCenter v2 controls before remote stage**.
Preserve the v2 fold0 plan/training/control manifest SHA256 values
`da8b9c0abef9f21c148766104539541a2d515bf10a4e5e7e7a7dcc49760cf835`,
`31b3ad9b403063c48179198d58e62978f61ac92650c3d42478653a241612d778`,
`e6aca868b4f41f32acb27770bdbee45bbc05080b4cb42d0b7b6e3d9e586fb2be`;
fold1 values
`f359a1f1e29bdbcce46227a2cac7af525265bddef6dd53bfd5437ddb2930c05e`,
`21f3b1907b30a98d1639afb806f46a90cc1849935252a8eabe6b300d90fc4acc`,
`4491c5abd6e0cb10a72277d28f89a61f6f26ede39c5107ec606dc8c040d7c4c0`.
The v2 handoff SHA256 is
`3018553ac4579d297f61b33c0261923941fd164eb3978a0975502cfd49b75116`.
V1 and v2 were not remotely staged or launched and remain unchanged.

The v2 controller recovery and source-frame checks passed local tests, but
its independent auditor's `pre_reservation_frames_bound` can return true for
an intentionally wrong `launch_intent` plan hash, lease ID, project, run and
token. The auditor also does not bind `launch_receipt.intent_sha256` to the
actual intent and accepts a frame receipt timestamp after the reservation.
These failures were reproduced in isolated scratch probes against both v2
auditors. Thus the claimed pre-reservation source measurement lacks proof of
identity and order even though the controller's normal path writes it.

Create distinct v3 fold0 and fold1 packages and attempts. In both independent
auditors, bind the full saved intent identity to the immutable plan, exact
lease/project/run/token, reservation receipt and launch receipt. Hash the
actual intent bytes and require `launch_receipt.intent_sha256` to match.
Require finite numeric timestamps ordered
`frame.at <= intent.at <= reservation.at <= launch.at`, together with the
existing exact source-frame map, source root, split, remote verifier and
receipt hashes. Reject missing, malformed, wrong-ID or out-of-order evidence.
Retain the v2 lost-reply recovery, one-shot release, pre-request source-Zarr
shape read, resource checks and no duplicate request/release semantics.

Preserve the source-only science: explicit split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`,
fold0 56 fit/15 inner source44 movies, fold1 102 fit/26 inner source6 movies,
two epochs, seed 2026, cold start, same trainer, source-inner BCE selection
and quality thresholds. No outer target GEFF/image access before frozen graph
and separate scoring. Recompute and seal every changed plan, training bundle,
control manifest and auditor SHA in new directories; never edit v1/v2.

Adversarial local tests must reproduce both v2 false accepts, reject each
wrong intent field and wrong launch intent hash, reject late/nonfinite order,
and pass a fully bound valid chain. Repeat v2 recovery tests, full source
hash/manifest readback and no-cache compilation. Require independent second
review before any remote stage. Later x138 assembler SHA pins need a distinct
version. This prereg is local only: no SSH, queue/GPU action, target read,
Kaggle POST or OOF claim. The primary full fold0 lease remains untouched.
