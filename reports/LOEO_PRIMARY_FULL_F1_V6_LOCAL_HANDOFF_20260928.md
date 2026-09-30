# Primary full fold1 v6: local manual-release handoff

Status: **LOCAL PACKAGE READY FOR INDEPENDENT REVIEW; NO REMOTE STAGE, QUEUE LEASE OR RUN**.

## Immutable identities

- Pre-registration `LOEO_PRIMARY_FULL_F1_V6_MANUAL_RELEASE_PREREG_20260928.md` SHA256 `aee32317d4864ab235883290b446f3ea20bcd8d952bc98b763e99a289ba56e1c`.
- Rejected v5 read back unchanged: plan SHA256 `4f05dd6ca846c849ed0566b932e3453d0e9187a5b291de0bee07030ab3f98ac0`; 21-file manifest SHA256 `d60672f1df3b3f3aa0fe716b06b0760642b6e043cb7213cdaccfbd953df79219`; controller SHA256 `774c0e55737fed650b3b4c4b60f4b97388d6dff302fd3c5ebaa44723c5efc157`; auditor SHA256 `265e5d3844d29c5ad977013fa4051d83d8df5e3f7e1df10816437fd250242fa7`. V1 through v5 were not staged or run.
- New local package `work/loeo-primary-full-f1-v6-20260928/`; attempt `75be66f1acf8`; lease ID `loeo-primary-full-f1-v6-75be66f1acf8`.
- `full_plan.json` SHA256 `51bff74097e56c42cb9a8b00d1edec80b555e101913f1423cc9c85ffaa9ea224`.
- 21-file `full_bundle/bundle_manifest.json` SHA256 `857b712521801d16948c51b32f430bb40f73965a09e4371681e1b8ee4f1ef5f1`.
- `full_control.py` SHA256 `f3648897bc500f9af0e9d04ff7c4ff6f226929503ec2dc57d9a10c46f9e1de5b`.
- `audit_completed_full.py` SHA256 `1b40e92766d34c3854817590cf43c6fb85a7c1fdf47a2c7915056d44603dd723`.
- Bundled `full_supervisor.py` SHA256 `d72dd630d145644843f31482e7cf33ec548435cec92a1c2b0118c9cfaa91f220`.
- Local test source SHA256 `d9f173b10dd7a1e566bb84264db57e05a19ca316ce6556390aeac990c63442e6`.

## Correction

The post-run manual release now saves exclusive fsynced `full_manual_release_intent.json` before any queue release. It binds plan SHA, lease ID/token/run/GPU, pinned reservation SHA, exact live active row, matching launch/exit PID and start, stopped process/group and empty GPU probe, supervisor-attempt absence and time. Both manual and unlaunched intents block every later automatic release from any queue state. A prior supervisor claim, release intent, reply, complete receipt, release control, or unreadable marker blocks manual release.

The remote supervisor and manual recovery acquire the same exclusive `run/supervision/release_claim.json` before a release. A supervisor claim or manual claim wins once; the other path cannot issue a queue release. Supervisor release writes its own exclusive intent and preserves raw reply/error before completion. Manual release saves raw reply/error, then requires exact raw `id` and `state=RELEASED`, a fresh full-identity live `RELEASED` row with real `gpus=[]`, a fresh empty GPU/run-owned-process probe and the same stopped launch/exit identity. Missing, malformed, foreign or uncertain raw replies remain unresolved without retry.

The final independent auditor binds manual intent, raw reply, remote claim, pinned reservation and release-time pre/post probes to the live released row. It also binds a supervisor completion to its claim, intent and raw reply. The 28 named final checks remain unchanged.

## Local validation

- `python -B -m unittest -q test_full_local.py`: **43 tests passed**. The tests reproduce v5's two manual release calls after two lost replies, then show v6 issues one call across repeated reconciliation for lost and malformed replies. They cover exact positive raw/live success, foreign replies, supervisor uncertain-response/complete markers, a claim race, cross-branch guards, and supervisor one-shot timeout, along with all v5 queue and science tests.
- No-cache `compile()` passed for all eight local Python sources. Read-only parsing validated the remote supervisor probe and manual claim scripts without SSH.
- `python -B build_full_bundle.py validate-inputs`: 128 source, 71 outer, 13 support files.
- Full post-build byte/SHA readback passed for all 21 manifest entries, bundled source copies, plan SHA and manifest SHA. Science remains 102 fit/26 inner source `6bba`, 71 excluded outer `44b6`, 9,949/2,443 windows, 50 epochs, seed `20260930`, cold start and unchanged gates.

## Remaining gates

Independent second review must accept v6 before stage. A distinct later x138 version must update assembler pins. This correction did not use SSH, queue/GPU actions, outer images/GEFF, Kaggle POST or OOF data. The active primary fold0 lease was untouched.
