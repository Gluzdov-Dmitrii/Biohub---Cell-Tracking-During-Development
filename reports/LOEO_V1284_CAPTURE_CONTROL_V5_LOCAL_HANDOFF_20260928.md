# V1284 capture control-v5 local handoff — 2026-09-28

Control-v5 is a distinct local-only successor for the unchanged source-v4
capture package. No source science, capture boundary, target GEFF access,
remote stage, queue mutation, GPU launch, Kaggle POST, EXPERIMENTS.md or
current-state report changed.

## Seals and scope

- Source-v4 `work/loeo-v1284-source-capture-v4-20260928/package_manifest.json`:
  SHA256 `31d1a8c632c5cee711772e784a023bca377d4b9863a2ef9c3760a1aa54c8e55d`.
- Parent blocked control-v4
  `work/loeo-v1284-capture-v4-control-v4-20260928/control_manifest.json`:
  SHA256 `8a555620d025665b88e0b09013fe89c37c25c190eb6b745a9fb1a52257273bb7`.
- Preregistration
  `reports/LOEO_V1284_CAPTURE_CONTROL_V5_REQUEST_RECOVERY_PREREG_20260928.md`:
  SHA256 `bdf327d357b57cc8918a5dd739c49b431809731d53d1aa891e71cef23f6ebdb0`.
- Queue-shape/process-probe addendum
  `reports/LOEO_V1284_CAPTURE_CONTROL_V5_QUEUE_SHAPE_ADDENDUM_20260928.md`:
  SHA256 `a53152274a75c8ed1859680a3457ed8e82e5eb2628fe27110f9efd428614e460`.
- New control-v5 package
  `work/loeo-v1284-capture-v4-control-v5-20260928/control_manifest.json`:
  SHA256 `9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`,
  schema 5, purpose `v1284_capture_v4_one_shot_control_v5`, seven files.

The new controller fsyncs an exclusive request intent bound to the exact
prepared config, plan, lease, token hash and resources before a raw queue
request. It saves raw replies before parsing. Lost/nonzero/malformed replies
and WAITING are reconciled against one exact live row; reconciliation never
reissues a request. WAITING cancel and unlaunched RESERVED release each have
their own fsynced one-shot mutation intent. A prior intent blocks duplicate
mutation when its reply is lost. Release requires an absent run, no run-owned
or unreadable own processes, a physically idle assigned GPU, and a fresh
exact queue row. The normal launch requires an exact RESERVED response and
live reservation before any remote child starts. The watcher binds its
release with a separate fsynced intent.

The independent completion now includes SHA256 bindings for sibling
`request_intent.json`, `request_response.json`, `reservation.json`,
`partial_launch.json`, and `watch/release_intent.json` in `runtime_audit`.
The downstream head audit must recompute those sibling hashes rather than
trust the completion alone. Source-v4's sealed runtime audit outcome string
remains `PASS_CAPTURE_V4_RUNTIME_RELEASE_CONTROL_V4`; the completion pins
the actual control-v5 manifest separately.

## Local validation and release gate

`python -B -m unittest discover -s
work/loeo-v1284-capture-v4-control-v5-20260928 -p test_control_local.py -v`
passed 29 tests. The tests cover normal launch/watcher from arbitrary cwd;
lost request, cancel and release replies; returned WAITING; malformed and
nonzero replies; WAITING-to-RESERVED race; missing/foreign rows; busy GPU;
run-owned or unreadable process; repeated reconciliation; audit lineage; and
source-v4 verifier compatibility. A separate exact-byte readback passed all
seven manifest entries, parsed all six Python files as AST, found no cache
files, and rechecked both unchanged parent manifests and both v5 prereg files.

Independent second review of control-v5 and the downstream head-audit
successor is required before a fresh source-v4 attempt is sealed or staged.
After any future exact stage, run the sealed source-v4 CPU canary and compare
both generated LF hashes before requesting a GPU. The downstream head audit
must pin this v5 control manifest and use actual terminal `RELEASED` queue
shape with `gpus=[]`. Any ambiguous queue response remains unresolved and
must be handled by read-only reconciliation without a second request,
cancel, or release.
