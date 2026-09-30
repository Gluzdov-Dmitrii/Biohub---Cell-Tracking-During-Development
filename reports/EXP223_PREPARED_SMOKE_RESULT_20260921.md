# EXP223 preparation and smoke result — 2026-09-21

PASS immutable4weight SHA verification, remote weights_only load and source imports. PASS leased source-only GPU smoke, graph/schema/integer/bounds checks and sealed175 cohort routes. Full175 inference **not launched**.

Remote code: `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp223_horaz0_v1_20260921`.
Remote run: `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp223_horaz0_source_smoke_20260921`.
GPU04efb7bd-1f45-38cd-4a13-c79b6aeaa002; wrapper550656, child550657/start519606776; exit0, no timeout. Process/group/GPU absent; monitor receipt records RELEASED_AFTER_VERIFIED_EXIT and queue RELEASED. No active EXP223 GPU lease.

Selected fold0 model source6bba_05b6850b first16frames:6.4435513s inference,1027nodes/956edges, peak995589632 CUDA bytes. CSV SHA14277b20730c60cb933132828d9f92d79494a8e201405e459486ad38895887e8. This is the smallest source volume, not representative175 benchmark and not target scoring. No GT read; audit-hook denies.geff.

175cohort sealed:59 target44b6 ->fold0,116 target6bba ->fold1;17500total frames. Manifest SHA001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4. Two prereg arms selected50/20 and fixedlast50 with SAME selected-source decoder/config; all arms complete before target scorer. Original fixedlast source/config retained solely as immutable artifact, not substituted into epoch control.

Evidence receipts: exp223_download_20260921.json; exp223_safe_load_probe_20260921.json; exp223_smoke_staging_20260921.json; exp223_smoke_latest_20260921.json; exp223_source_smoke_config_20260921_monitor.json; exp223_graph_and_cohort_gate_20260921.json. Preregistration: EXP223_HORAZ0_PREREGISTRATION_20260921.md.

Next action: implement experiment-owned resumable no-label heldout inference runner reading sealed manifest; per-movie immutable CSV+hash+graph gates, single fold model only, abort on any inconsistency. Keep source/config fixed for both arms. Add runner-specific900s representative-source benchmark on a larger source volume before selecting <=3h chunk size. Current smallest16frame runtime cannot justify a full175 ETA; arithmetic minimum about2h/two arms but not a forecast because volume/ILP complexity vary. Follow with leased<=3h chunks and remote supervision; label scoring only after BOTH complete. No training and no Kaggle POST.

Existing exact read-only recheck command: `python scripts/probe_exp223_smoke.py`. Do not rerun `launch_exp223_smoke.py` against existing run/lease. No full-run launch command exists yet: missing production runner/runtime sizing is the remaining implementation gate, not an access approval blocker.
