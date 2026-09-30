# EXP223 comparable OOF running — 2026-09-21

Full-cohort protocol is frozen and first chunk is RUNNING. Horaz selected50/20 and fixedlast50 use identical selected decoder/config and each target embryo's heldout model only. 175movies per arm,350predictions; same EXP214/EXP222 cohort. Neither author199 result nor custom metric is used for comparison.

Production source remote `code/exp223_horaz0_inference_v3_20260921`; code_manifest SHA037dc7fb367948cd1253f7ac44dab95f2c23c686e259462b8b446f2ea37da8cd; parent cohort SHA001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4. PlanSHA passed as command argument, code manifestSHA inside pinned plan; every code/model file verified. NoGT audit hook rejects.geff. Per-movie CSV verified for integer parsing, image bounds, unique rows/nodes/edges, temporal adjacency, in<=1/out<=2. Resume requires exact contract+CSV hash+graph; corruption/unreceipted existing CSV aborts, never silently recomputes. JSON receipts/completion atomic. Seven unit testsPASS including negative routing/hash/graph/resume corruption. Source-only remote benchmark is integration evidence.

Representative100frame source6bba_07e24132 (100x64x256x256):139.4737s,47860nodes46301edges,peak999540224CUDAbytes; exit0 and independently remotely RELEASED. This is one dense source example, not worst-case runtime proof. Estimated350predictions~13.6GPUhours; practical first estimate10–20GPUhours, conservative hard maximum24GPUhours across8chunks before review. With1GPU allow~14–24h plus scheduling/scoring;2GPUs~7–12h once available. No automatic retries beyond that budget.

8strided frozen chunks:00–06 each22movies x2arms,07 has21 x2arms. Each wrapper cap10800s,8CPU32GiB. Frozen manifests/configs: reports/exp223_full_rollout_20260921.json; reports/exp223_chunkNN_config_20260921.json. No target labels until all350unique receipts complete+validated. Final scorer must replay exact official EXP214/EXP222 evaluator and verify baseline counts/weighted aggregation; source baseline script/evaluator current hashes recorded reports/exp222_remote_current_hash_audit_20260921.json. Fixedlast same decoder remains development-adapted due historical decoder tuning.

## Live receipt

Chunk00: lease exp223-horaz0-pair-chunk00-20260921; GPU04efb7bd-1f45-38cd-4a13-c79b6aeaa002; wrapper551777, child551783/start519725971; remote observer551778 on ngpu01; remote controller360214 on prepost. Fresh queue RUNNING/CURRENT and remote heartbeat verified reports/exp223_chunk00_status_20260921.json. No Windows monitor dependency. Remote controller releases only after exit receipt and no child identity/group/GPU processes. Remote supervision bounded200min; child3h cap. Errors/stale observations keep lease, never unsafe release.

Source8 uses GPU61c and is still RUNNING, control8/domain5 at last check; no chunk01 launched while bothGPUs occupied. Chunk01–07 are PREPARED, not automatically queued/running. Rollout currently depends on next authorized heartbeat for subsequent launches, while each active chunk runs/supervises remotely. Parent may add finite automatic dispatch later; do not claim it exists now.

## Exact continuation

1. `python scripts/check_exp223_chunk.py 0` refreshes active chunk; check other active chunk similarly.
2. Confirm fresh shared queue capacity and no other project waiting. After source8release or chunk00release, launch next **unlaunched** frozen chunk: `python scripts/launch_exp223_remote.py reports/exp223_chunk01_config_20260921.json` (then02..07 as capacity opens,max2totalGPU). Launcher refuses any existing lease ID; on partial RPC failure reconcile saved reservation/partial launch receipt, never blindly retry. Keep CPU affinity separate if2GPU runs; set second freeCPU slice before launch based live allocation.
3. On timeout/failure, preserve all receipts and diagnose; no automatic extra quota or target scoring. Resuming valid outputs is supported but requires explicitly prepared new bounded wrapper/run pointing to prior output, with ownership and immutable hashes reconciled.
4. After8chunks complete+released, implement/run one official scorer gate validating exact350 receipts before GT. **Official scorer glue is still pending**; do not use author custom scorer or score first completed arm early. Expected columns/statistics: both arms vs baselineDL and classical, aggregate adjusted edge Jaccard+division term, per-embryo counts, node recall,FP/FN,divisions, paired movie deltas. Current baseline scores remain DL0.7427291486/classical0.7409785649.

## Operational continuation — 2026-09-21 later user request

Chunk00 COMPLETE44/44 predictions,exit0/no timeout,3212.500955s total(~53.5min), remote RELEASED_AFTER_VERIFIED_EXIT. Freshly recomputed44CSV SHA all match receipts; actual CSV columns verified: id,dataset,row_type,node_id,t,z,y,x,source_id,target_id. Evidence exp223_schema_and_next_launches_20260921.json (sample full per-movie receipt included).

Fresh queue had no active/waiting jobs. Launched two next sealed chunks with disjointCPU:
-01 GPU61c0078d-a4a6-37a2-3aba-0378e7794c46 CPU0-7: wrapper557843,child557849/start520974288,observer557844,controller360867.
-02 GPU04efb7bd-1f45-38cd-4a13-c79b6aeaa002 CPU8-15: wrapper557921,child557927/start520976232,observer557922,controller360894.
Both remote supervisors RUNNING/CURRENT verified;3h cap each; no local process dependency.03..07 remain pending, no retries or new timer. Existing24GPUhour total hard ceiling unchanged. First completed chunk suggests~7.1GPUhours whole cohort if others similar, but do not treat it as guaranteed ETA.

Scorer contract: immutable code_manifestSHA037dc7fb367948cd1253f7ac44dab95f2c23c686e259462b8b446f2ea37da8cd; pinned cohortSHA001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4; decoderSHA6854b15c8facdb7216e8546fe8f461d2c673770b032fdab6a4e5bbc3b6d508fe. Root `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development`; each `runs/exp223_horaz0_pair_chunkNN_20260921/output/{arm}__{dataset}.csv` has same-basename.json, plus complete.json records. Receipt contract includes arm,dataset,fold,mode=heldout,weightSHA,manifestSHA,decoderSHA,codeSHA; top-level csvSHA,shape,counts,seconds,stats. Expected175unique dataset per arm across all8chunks,350total; both arms completion and exact ID/routing/hash/graph checks before anyGT. Output schema is original10competition columns; IDs restart per movie, so combinedCSV must reindex global row ID if scorer requires it. Scorer implementation delegated elsewhere, no scoring in this operational task.
