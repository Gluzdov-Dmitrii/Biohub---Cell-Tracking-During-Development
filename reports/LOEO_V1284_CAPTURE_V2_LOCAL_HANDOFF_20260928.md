# V1284 source-image capture v2 — local correction handoff, 2026-09-28

**State:** local code and synthetic validation only. No real checkpoint was
loaded, no source or target GEFF label was read, and no SSH, stage, queue,
lease, GPU, Kaggle or scoring action occurred.

V2 implements `reports/LOEO_V1284_CAPTURE_V2_CORRECTION_PREREG_20260928.md`
SHA256 `64b9905999120c456c7154587c47a0240bdf558fb10bbd4f488dbf1a1e35964c`.
The rejected v1 package remains unchanged: its manifest SHA256 is
`15bb00405aa8caec4090a7cb45291f02787207d8970d8b047b13bf48b543b38e`.
Use only the distinct v2 directory and new v2 attempt identity for later work.

## Source and repair

The copied executed x138 notebook's 12 code cells reconstruct its source.py
byte-for-byte, SHA256 `eace83c4e4ec8f967aa03edf516acdbb3eb35bbcfaf02fbef93465fa26680775`.
Cells 0–1 remain byte-identical; only cells 2–4 differ. The sole generated
predictor delta from v1 is one capture-mode branch immediately after
`predict_video(...)` returns and before x138's `_CACHE_DIR` block:

```python
        if os.environ.get("V1284_MODE") == "capture":
            continue
```

The original noncapture cache, `build_graph`, ILP and `save_graph` path remains
byte-identical: removing those two new lines from the v2 predictor restores
the v1 predictor SHA256 `e777b9f5e79c40c2f40a29d23ebdeaf1945a5eb33c5bf6b02645d90adf19aed0`.
`_v1284_refine` writes first-seen nonempty and empty frame shards inside
`predict_video` before this branch; every capture movie continues to the next
without `.geff` creation. The all-path GEFF denial remains in `capture_guard`.
The exact one-time text anchor and AST compilation guard the generated patch.

V2 package: `work/loeo-v1284-source-capture-v2-20260928/`.

- 27-file `package_manifest.json` SHA256 `ef81cb60c9ebe9cbe7760dbc189d840f26b338fe101a6bb0c0d7648d742733f1`.
- `capture_cells.json` SHA256 `eabb04f72c57bc33bec4f266d14bc15e6be77e9df451b3b30f5b9fafb45d4e2b`.
- `capture_cells_manifest.json` SHA256 `b13e1213c71d60aebf74162cfec9e54725d454cc3c315d04e0653fd7a08599d6`.
- Generated v2 predictor SHA256 `7f0997565a26ec2f819039fd857f912cef03d72dd21c31d0167e004d596638b4`; unchanged head-free V1284 feature module SHA256 `db22bcf2cd7d54dda021302c281b224ef517508e53f2aaa7c75fd47b6fe11e8a`.

The plan schema/purpose and identity now say v2, pin the correction prereg
and rejected v1 manifest, and retain the same source-only fold IDs, separate
quality-audited fold primary/secondary checkpoint prerequisites, loaded SHA
recording, forbidden-head guard, empty-frame contract, and independent
release/exit/shard audit. V2 does not relax the no-GEFF access guard.

## Validation and remaining gates

`python -B -m unittest discover -s work/loeo-v1284-source-capture-v2-20260928 -p test_capture_local.py -v`: **8 passed**. A discriminating test executes the patched per-movie `predict` function over two synthetic source movies. Each movie writes one nonempty and one `(0,4)/(0,224)` empty shard; `build_graph` and `save_graph` traps are never called. The same function without capture mode reaches both graph saves. Other tests cover source reconstruction, generated patch order/hash, strict GEFF/opposite-prefix/checkpoint guards, missing/extra/wrong-time/nonfinite/malformed shards, plan audit roles and release timing. All eight Python files and five capture cells AST-parse; package inventory, source, split, support and generated-code hashes read back exactly; zero `__pycache__` directories exist.

The first real v2 plan still requires independently audited, quality-passing
source-only primary and secondary checkpoints for the same fold. A separate
controller must later enforce fair queue, physical-idle A100, exact staged
readback, bounded launch and release-time GPU-empty evidence. Linux source
symlinks, runtime dependencies, actual CUDA capture, head refit, outer image
inference and graph scores remain untested and unclaimed. No source GEFF label
matching can begin before the independent capture verifier passes.
