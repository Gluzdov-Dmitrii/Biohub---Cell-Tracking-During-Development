# EXP209 current-organizer rescore: readiness and reconstruction v1 plan

Date: 2026-09-27. This is a preregistration for a **new, versioned CPU-only
graph reconstruction and score attempt**, not a current-organizer score or an
authorization to launch. The original EXP209 175-movie historical result stays
`0.6815218332750073` under its historical evaluator. The sealed EXP209 result
archive has 38 JSON/log entries and no final graph files or final-graph SHA256
receipts. Local readiness receipt
`reports/exp209_current_metric_rescore_readiness_20260927.json` therefore says
`BLOCKED_NO_SEALED_FINAL_GRAPH175`, `current_organizer_score=null`.

## Evidence and feasibility

The archive manifest SHA256 is
`1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a`.
Its 38 entries rehash exactly, as do the historical result, EXP214 frozen rows,
historical result/cleanup receipts, source trainer manifests, and pinned current
organizer code. The 116 forward `6bba` and 59 reverse `44b6` selected movie IDs
are unique, match the frozen EXP214 rows, and are opposite the corresponding
source trainer's ten training plus two checkpoint-validation movies. This is
historical reciprocal embryo-held-out evidence, with the policy family already
development-adapted; it is not pristine untouched OOF.

Read-only metadata and SHA256 checks on the original remote paths found all
175 prefinal EXP192 raw candidate NPZs, 328,921,296 bytes, matching hashes in
the EXP209 chunk results; all 59 reverse EXP191 selected-edge gap NPZs,
24,328,164 bytes, matching their three `gap_filtered.json` manifests; and all
175 image Zarr directories and image-array paths. The image content was not
rehashed on this visit. Forward/reverse detector checkpoint hashes are
`dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb`
and `5c0f8358389af40a646a0fe3b4e8e88fb1b1c155da12e92efa3c944eeb499366`;
reverse DeepCenter is
`ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e`.
All three still match on disk. They are provenance pins; cached-candidate
reconstruction does not need to rerun the detector or DeepCenter. Exact
read-only cache, code, image-audit and checkpoint pins are recorded in
`reports/exp209_reconstruction_feasibility_inventory_20260927.json`.

The original EXP209 selected forward graph can in principle be rebuilt on CPU
from the frozen candidate coordinates, image intensity centroid radius
`(3,5,5)`, registered links and minimum track length 8. The selected reverse
EXP191 graph can in principle be rebuilt from frozen gap selected-edge caches
and minimum track length 6. The existing evaluation scripts interleave these
operations with GEFF and track reads, so a separate label-free extractor must
be written and tested. The original final graph bytes and SHA pins remain
**missing**. A reconstructed graph must be reported as a new reproduction,
even if its historical metric rows later replay exactly.

## Frozen v1 execution contract, before any labels

1. Use a new sibling run namespace such as
   `runs/exp209_current_metric_reconstruction_v1_20260927`; never overwrite or
   edit EXP209/EXP192/EXP191 runs. Root reviews the exact new source and its
   hashes before any launch. CUDA remains hidden; CPU only. Pin the eight
   `movies.json` SHAs from the EXP209 structural gate, all 175 candidate-cache
   hashes, three reverse `gap_filtered.json` SHAs and 59 arm-cache hashes,
   source trainer splits, original reconstruction-function hashes, and the
   EXP192 image content manifest SHA
   `ddf71e7f5cf52a0da152ef8fe32a8e1ff505e8534184a084b04e2e1b9a673add`.
   Recheck current image content against the historical image audit before
   using pixels. Pin the new exporter, serializer, environment and runner
   hashes in a fresh receipt.
2. Implement a label-free extractor. It may read only cached NPZ, image array
   and nonlabel scale metadata. It must not call `open_dataset(...,
   require_tracks=True)`, `GeffMetadata.read`, `dataset.tracks`, or any metric.
   Freeze exactly the original forward radius/min8 and reverse gap/min6 rules;
   do not select a new arm from target labels. Emit one canonical graph file
   per selected movie and a per-graph SHA256 receipt, including node/edge
   counts, finite/coordinate bounds, directed time order, parent count and
   dataset ID. Compare label-free counts and centroid/filter telemetry with
   the historical chunk receipts where available.
3. Before any label access, verify all 175 IDs exactly once in the 8 frozen
   chunks, every graph/receipt hash, zero extra outputs, exit code 0, no
   timeout, and process/CPU resource release. Write and durably sync a
   `no_metric_gate.json` with all graph hashes and source pins. Any ambiguity
   stops. No graph may be replaced after this gate.

## Ordered score gates after a future root review

4. Only after the full no-label graph/hash/release gate passes may a separate
   CPU scorer open the 175 target GEFF labels. First run the pinned historical
   evaluator on the newly sealed graphs. Require every historical selected
   per-movie metric row to match the frozen EXP214 rows to `1e-12` and the
   pooled historical result to match `0.6815218332750073` to `1e-12`. If
   any row differs, stop and preserve the failure receipt; do not compute a
   current score. Historical replay is a behavioral check, not proof of
   equality to unpreserved original graph bytes.
5. If historical replay passes, score the same immutable graphs with the
   current organizer metric pinned to `metrics.py` SHA
   `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`,
   `division_metrics.py` SHA
   `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`,
   tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, and
   organizer metric commit `075fc5f5a52d11077f9dc2b074644618f26939e2`.
   Report a new current-metric score with explicit evaluator identity and the
   development-adapted reciprocal evidence class. Never relabel the historical
   `0.6815218333` as a current-organizer result.

The historical EXP209 runner used CPU affinity 0–7, a 16 GiB RAM budget and
no GPU. Archived result mtimes from the first forward chunk to the final
reverse chunk span about 28 minutes; this excludes the first forward chunk's
runtime and is not a benchmark for the new extractor or current metric. A
practical initial budget is tens of minutes on eight CPU cores plus image
integrity I/O and metric runtime, to be bounded explicitly before launch.
No reconstruction job, historical replay, current score, target label read,
GPU reservation or Kaggle POST has occurred in this preparation.
