# V1284 fold0 source-v4/control-v5 CPU stage handoff — 2026-09-28

Status: **PASS_V1284_F0_V4_CPU_STAGE_CANARY_NO_QUEUE**. The fresh identity is
`loeo_v1284_capture_f0_v4_ba382850b115`, lease ID
`loeo-v1284-capture-f0-v4-ba382850b115`; both differ from the failed v3
attempt. There was no queue request, GPU launch, target GEFF read, graph
score, outer OOF claim, or Kaggle submission.

The immutable local completion receipt is
`work/loeo-v1284-f0-v4-cpu-stage-20260928/loeo_v1284_capture_f0_v4_ba382850b115/cpu_stage_complete.json`
SHA256 `4c227c64b672e856cf5f5eeec8a9419a627e58603512150fcf01357f8a018133`.
It binds the exact staged evidence and prepared control config without
printing the lease token.

| Artifact / gate | Exact result |
| --- | --- |
| Source-v4 remote code | `$R/code/loeo_v1284_capture_f0_v4_ba382850b115`; 28/28 files, no extras/symlinks/cache, manifest SHA256 `31d1a8c632c5cee711772e784a023bca377d4b9863a2ef9c3760a1aa54c8e55d` |
| Inert remote control-v5 copy | `$R/plans/loeo_v1284_capture_f0_v4_ba382850b115.control-v5`; 7/7 files, manifest SHA256 `9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2` |
| Source/control archive transfer | Local archive SHA256 `e19df7bc90f864b47f67435661dff5d73ccad18e701472040d9d4312dabbfd1c` / `20977c45e8d3e62425c0e4f38fca42d2a89b632acbb90786f6d03e8762e4b62b`; remote byte/hash readback matched |
| Fresh plan | `$R/plans/loeo_v1284_capture_f0_v4_ba382850b115.json`, 6,824 bytes, SHA256 `118fb1418a1f9367edfe8723d715f6ebe6d7a807752dac9d2f1fbb9b50137a5b`; local binary copy identical |
| Independent plan/source check | Production Python `validate_plan` passed all six audited model/audit files, 71 approved `44b6_*` source-image symlinks, 128 disjoint `6bba_*` outer IDs, absent run; corrected diagnostic receipt SHA256 `ee0b4374e9d5b228e5727b1eb3b2862181b7611e99d3eb9214ea48ef320fdc2e` |
| CPU canary | `PASS_V1284_V4_CPU_PATCH_HASH_CANARY`, `model_launch=MOCKED_ONLY`, real child import PASS. Predictor LF SHA256 `330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e5`; module LF SHA256 `940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`; LF and CRLF inputs generated identical bytes; canary receipt SHA256 `9b200fd5b123210de606127328417295845ca63bf3feed4ae66f29b30c1963e5` |
| Local control-v5 preparation | `PASS_LOCAL_PREPARATION_NO_LEASE`; private config SHA256 `19cd1e1e48c12fd34a40a47ba240cadced19eba782bcc9c0f5ba7b400b2327b7`, preparation receipt SHA256 `902b4154244f24dc77796aa971c255e0701db5c282cd4b022ef5f0cb884aa262`; one A100 physically idle at that snapshot, all required modules present |
| Final live queue and run | Read-only compact status: 373 rows, zero exact lease-ID matches; final remote source/control/plan hashes retained and run absent |

`R` is `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development`.
The local prepared config is under the completion receipt directory at
`control-prepare-v5/control_config.json`. It contains the private queue token;
use only the absolute file path with the sealed controller. The remote
control copy is byte evidence and is not executed on the cluster.

The first independent remote plan readback diagnostic generated a malformed
read-only script by replacing `PLAN` inside its own status string and failed
with `SyntaxError`. Its error receipt is preserved, SHA256
`c9ba36b4f7e87ac7937af9a7339fd74477a90985ba9064665a1a348e77e119ae`.
A distinct corrected readback used a collision-proof literal parameter and
passed; no staged source/control/plan file was changed by either diagnostic.
Earlier queue-status timeouts and their receipts are likewise preserved; a
fresh compact call to the same live queue CLI passed before stage and again
after the canary. Neither status call mutated the queue.

**Stop at this handoff.** The idle-GPU and queue snapshots are volatile.
Any future GPU decision requires explicit authorization, fresh live
control-v5 launch preflight, one durable request intent, and the v5 one-shot
reconciliation path for ambiguous replies. No second attempt or new plan
may overwrite this staged identity. Independent terminal capture/release and
feature-shard audits remain required before head refit; the downstream
head-audit successor has its own gate.
