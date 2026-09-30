# EXP209 reconstructed-graph scorer v1 — local handoff, 2026-09-27

Status: **PREPARED_LOCAL_ONLY_NO_LABELS**. This package has not been staged or
run. No target GEFF, historical metric, current metric, GPU, or Kaggle POST was
accessed or executed by this preparation.

## Fixed input and evidence class

- The separate EXP209 CPU reconstruction's completed `no_metric_gate.json` is
  pinned by SHA256 `8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1`.
  Its reconstruction bundle manifest and contract are pinned by SHA256
  `cdf49fad597f1dcc47e65d841cc894ed2be439f45f4bfe1838e790b390c8a311`
  and `3860dce507c02b49386414a26c51071f6ff993e8b49476dc46e2b232973e8dd0`.
- The original EXP209 selected 175 per-movie rows and pooled selected score
  `0.6815218332750073` are in the archived
  `forward_plus_exp191_confirmation.json`, SHA256
  `bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c`.
  The 116 forward rows use source44b6 to evaluate target6bba; the 59 reverse
  rows use source6bba to evaluate target44b6. The source-only frozen policy is
  forward centroid radius `(3,5,5)` plus min8, reverse EXP191 saved gap edges
  plus min6.
- The eventual score's evidence class is **leakage-controlled reciprocal
  evaluation with historically exposed target labels**. The original EXP209
  final graph bytes and hashes were not retained. Matching historical rows
  would establish behavioral replay of **new reconstructed graphs**, not byte
  identity with those original graphs or pristine untouched OOF.

## Gate and score order

1. Verify the scorer bundle manifest and config SHA, then the original CPU
   reconstruction bundle, contract, and completed graph gate SHA. Rerun the
   label-free eight-chunk verifier: all 175 canonical graph CSV and receipt
   hashes, exact ordered IDs/row counts, finite image bounds and directed
   graph invariants, input/image hashes, worker exit0/no-timeout/absent identity,
   and RELEASED controls must match the persisted gate exactly.
2. Rehash the actual image Zarr tree for each movie and independently reexecute
   the frozen EXP209 source functions on every pinned raw/gap cache. This
   compares all selected historical centroid/filter telemetry and computes
   canonical CSV bytes again. Every new CSV SHA must equal the sealed graph
   SHA. Metadata-only validation pins the isolated Python runtime and
   tracksdata commit. Write and fsync the scorer's own one-shot
   `no_metric_gate.json` with `labels_read=false` before allowing any GEFF
   operation. The GEFF path audit denies accidental pre-gate opens.
3. Hash 175 GEFF label trees, then evaluate the **new reconstructed CSVs**
   with the pinned historical EXP209 evaluator. Compare every archived EXP209
   selected per-movie count exactly and each finite float within absolute
   `1e-12` with relative tolerance zero. Compare the archived pooled selected
   fields and score at the same tolerance. Persist
   `historical_replay.json` only on full PASS. Any mismatch writes a blocking
   failure receipt and stops before current-metric import or execution.
4. Only after the historical PASS receipt, run the pinned current organizer
   synthetic fork contract and evaluate the same sealed graphs under current
   organizer commit `075fc5f5a52d11077f9dc2b074644618f26939e2`. Recheck
   graph/receipt hashes before each score and label tree hashes after both
   passes. Write a one-shot result with explicit evidence class. This step has
   not been run.

The historical evaluator files have SHA256 `31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83`
(`metrics.py`) and `d1cf1e0a43009d02174f1699ce2aa28458a2220ac4b521731d3bcf31cf8c76be`
(`division_metrics.py`). The current organizer files have SHA256
`cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`
and `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`;
the isolated runtime pins tracksdata commit
`e13cf379b5127deeb8301ce56410fda35b5a3cf9`. The graph builder is the
torch-free EXP236 v2 adapter, with fractional EXP209 coordinates accepted by
the EXP209 verifier.

## Local artifact and validation

- Bundle: `work/exp209_reconstructed_scorer_v1_local_20260927/bundle`,
  14 payload files, manifest SHA256
  `2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb`.
- Config SHA256 `d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335`.
- Runner source SHA256 `72e24bc53128c1e35ffe7dc806c74ccf0ad36575b52c5d7753ee60e2b3771b79`;
  preparer SHA256 `3a30384641b67fd9720b9a6416cb815024ddc708e6d6101695cc6bd7f7f0a370`;
  tests SHA256 `43566f653a123a2b0a0942a55307251889f1703199f6cb21e4c0c63bc75e750f`.
  The full source list is in
  `reports/exp209_reconstructed_current_scorer_v1_local_prepare_20260927.json`,
  SHA256 `c6d0d6caa69caba9e94f51fa94c63afe147ca666eb77fb1f786ae47b16cd5993`.
- Seventeen focused synthetic tests passed with `--basetemp work/p209t`:
  local preflight/tamper, manifest/graph/receipt tamper, all175 canonical
  source replay/tamper, strict archived rows and pooled-summary projection,
  GEFF audit ordering, replay-before-current, and one-shot failure behavior.
  Source compilation and local bundle rehash passed. Tests used synthetic
  graphs only, without GEFF or metric execution.

After root review, a future one-shot launch would use the isolated remote
`envs/current-organizer-py311-e13cf-v1/bin/python`, with CUDA hidden and the
exact bundle/config hashes above:

```text
/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/current-organizer-py311-e13cf-v1/bin/python \
  /home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp209_reconstructed_current_scorer_v1_20260927/score_exp209_reconstructed_current_v1.py \
  --config /home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp209_reconstructed_current_scorer_v1_20260927/config.json \
  --config-sha256 d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335 \
  --bundle-manifest-sha256 2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb
```

The full source replay and two scoring passes have unmeasured CPU duration.
If the historical 175-row replay fails in the pinned current environment, the
current metric remains closed; investigate a separately versioned diagnostic
without weakening the frozen replay gate.
