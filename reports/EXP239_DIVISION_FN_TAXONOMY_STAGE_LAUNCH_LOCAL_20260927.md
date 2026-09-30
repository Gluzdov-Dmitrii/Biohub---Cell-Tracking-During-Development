# EXP239 source division-FN taxonomy: local stage and CPU handoff

Status: local preparation only. No remote preflight, stage or launch was called;
no GEFF, score output or reciprocal target label was opened by this work. No
Kaggle POST or GPU use. `EXPERIMENTS.md` was not edited here.

## Corrected sealed bundle

The initial local EXP239 bundle had inherited the EXP234 image-scale receipt,
which covered only 17 of the 19 source-inner movies. Before any remote action,
it was replaced by the verified exact source19 image-only receipt
`source_inner19_image_scale_audit_v2_20260927.json`, SHA256
`d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6`.
The audit, config, preregistration copy and manifest were resealed. The current
eight-file bundle is `work/exp239_source_division_fn_taxonomy_20260927/bundle`:
manifest SHA256 **`22e5679b66462bad6662c1e98384e9bec9c4a656e7bfd7caec145b5ac8e3abaf`**;
config SHA256 `24b93782a3e9a4e3ddad42e0a211a8ceac7d2e99a0fd8f34925678404f4cbad9`.
Older local EXP239 manifest hashes must not be staged.

## One-shot remote protocol

The review-gated stage script is `scripts/stage_exp239_division_fn_taxonomy.py`,
SHA256 `f13fa570b81b1c4dc6c5c8ae9d344ebc4a4cb83489834aa5995fdf2ae6e25bdd`.
It checks the exact local eight-file manifest and config. Its read-only remote
preflight requires both new namespaces absent, imports the exact pinned source
scorer gate modules in the current-organizer Python 3.11 environment and denies
all GEFF access. The mutation path writes and fsyncs a unique local stage
intent before any remote write, transfers all nested files as exact bytes,
checks their SHA256 and Python AST remotely, and performs a separate readback.
An existing intent or namespace requires reconciliation, not a retry.

The launch script is `scripts/launch_exp239_division_fn_taxonomy.py`, SHA256
`2acf35fa748e5f6eabf85cc94136e1a5d4a69578faad56f5590eaaa1fcf2c1e6`.
It requires the exact stage receipt, repeats read-only import and byte/AST
readback with the run namespace absent, writes and fsyncs a unique launch
intent, then starts one process. Its wrapper and the audit itself hide CUDA,
pin CPU affinity 24–27, cap address space at 16 GiB, cap CPU time at 2400 s,
and cap wall time at 2700 s. Wrapper exit evidence is written on success,
failure or timeout. The immediate launch readback checks the wrapper process
or an exit record. Neither script opens source GEFF or scores during staging.

Remote namespaces:

- Code: `code/exp239_source_division_fn_taxonomy_v1_20260927`
- Run: `runs/exp239_source_division_fn_taxonomy_v1_20260927`

From the local project root, the nonmutating dry runs are:

```powershell
python -B scripts/stage_exp239_division_fn_taxonomy.py --dry-run
python -B scripts/launch_exp239_division_fn_taxonomy.py --dry-run
```

After root review, the read-only remote preflight is:

```powershell
python -B scripts/stage_exp239_division_fn_taxonomy.py --preflight-only
```

Only after a passing preflight and root review, the one-shot mutation commands
are:

```powershell
python -B scripts/stage_exp239_division_fn_taxonomy.py
python -B scripts/launch_exp239_division_fn_taxonomy.py
```

Do not repeat either command on an uncertain result. Inspect the local intent,
remote namespace and readback before deciding how to recover.

## Local validation

Both dry runs completed without SSH; the stage dry run generated remote source
SHA256 `bfe7c29400f4e4dd4db21cca89b0c63146629c843e7041ded2f41e24fab70ef6`
and readback source SHA256
`3533cf688d56422585faa075dd5f7fcc229a41956f8d2298e187eb0cb324d4a4`.
The launch dry run generated remote source SHA256
`d8dde0ab945f7cebef340284d5ba2e278ca8b160a787ef3ee2e5066abd365881`
and readback source SHA256
`2a3039400930ccb06d5ffe2571573abbb062fcef421ba22f34dec82b7970dd97`.
Sixteen focused local tests passed, including all five synthetic FN stages,
exact byte payload and AST checks, source19 scale coverage, no-SSH dry runs,
CPU bounds, durable intent before simulated uncertain remote results, and
duplicate launch rejection. Tests used a workspace-local temporary directory.

The audit remains a 14-event source-inner diagnostic. It cannot select a
division threshold or qualify a submission. The future CPU result must replay
EXP227 source44 TP2/FP6/FN3 and EXP236 source6 TP1/FP9/FN8, partition all
11 FNs, and rehash source GEFF trees after read before any mechanism proposal.
