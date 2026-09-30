# EXP239 source-only division-FN taxonomy — preregistration

Status: local CPU bundle only. No source GEFF was opened by preparation, and no
reciprocal target label, remote stage/run, GPU claim, Kaggle POST, or submission
slot is authorized by this document.

## Fixed inputs and question

Use only the frozen epoch-10 EXP227 source44b6 inner8 and EXP236 source6bba
inner11 graph CSVs. Their per-movie CSV and receipt SHA256 values, checkpoint
hashes, scorer gates, and exact ordered IDs are sealed in the EXP239 config.
Both frozen graph code copies have identical Horaz `postprocess.py` SHA256
`7145e2470c17c65fa5535348c2073dffe5a12e4e72e7945aa3e08d326794ad0c`.
The question is why the current organizer misses source divisions, not whether
a new threshold improves a score.

The known current-organizer source counts are EXP227 TP2/FP6/FN3 and EXP236
TP1/FP9/FN8. Thus the diagnostic has only 14 annotated division events and
11 misses across 19 movies. The events are too sparse for threshold selection,
private-robust promotion, or a transfer claim. These cohorts are source-inner
training monitors, not untouched reciprocal OOF.

## Mandatory order and gates

1. Verify the exact bundle manifest, isolated Python 3.11 runtime, organizer
   `metrics.py` SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`,
   `division_metrics.py` SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`,
   tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, and the
   pinned directed-fork synthetic contract.
2. With all `.geff` access denied, independently run the already sealed EXP227
   and EXP236 source scorer `gate()` functions. They must recheck graph producer
   code/plan/checkpoint, exit and released lease, all 19 graph CSV/receipt
   hashes, IDs, bounds and graph invariants. Compare their freshly computed
   no-metric gates to the pinned original no-metric gate receipts. Recheck the
   exact source19 image-only scale receipt SHA256
   `d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6`
   and each Zarr metadata hash. Write and fsync `no_label_gate.json` in
   a new, otherwise absent output directory.
3. Only then allowlist the exact 19 source `.geff` roots. No reciprocal target
   `.geff` may be opened. Hash each source GEFF tree before and after its own
   read; the eight previously pinned 44b6 tree hashes must also match. Use the
   pinned organizer's `DistanceMatching` at 7.0 µm and its actual division
   evaluator. Reproduce TP/FP/FN 2/6/3 and 1/9/8, 14 GT events, and 11 FNs
   before writing a PASS result. Any mismatch stops; retain the gate and logs.

## One mutually exclusive category per missed GT event

Classify in this fixed order, using the organizer's per-division matched window
and local directed-fork functions. A matched parent side is the GT dividing
node or its immediate predecessor. A daughter lineage is the GT child or its
immediate successor.

1. `no_parent_side_match`: no predicted node matches the parent side.
2. `fewer_than_two_daughter_lineages`: parent side exists, but fewer than two
   distinct daughter lineages have a matched predicted node.
3. `no_local_fork`: both sides are represented, but no predicted fork lies at
   a matched parent-side node or one of its direct successors.
4. `directed_branch_failure`: a local fork exists, but none has parent-side
   evidence plus matches from two GT daughters on distinct direct-child
   branches (child or grandchild evidence).
5. `organizer_veto_or_pairing`: a directed fork exists, but the organizer rejects
   every such fork as malformed/cross-component, or a valid candidate loses
   the organizer's one-to-one bipartite pairing. Report the subtype separately.

Count each TP as `recovered`, separately from the five FN categories. Emit
event rows with dataset, GT divider ID, category, match and candidate-fork
counts, subtype; per-movie and per-cohort category counts; pinned hashes and
source-label before/after tree hashes. Require categories to partition all
source FNs exactly. The final graph cannot reveal which internal Horaz repair
filter rejected a candidate; do not call these categories causal filter
attributions. The all-frame `safe_divisions_added` stats (240/188 in the
source8/source11 graph receipts) are not labelled true-positive counts.

## Interpretation and next step

This is one descriptive CPU diagnostic with no candidate graph, parameter
sweep, model selection or Kaggle submission. A concentration of covered-node
topology misses could justify a separate, preregistered hidden-compatible
mechanism if the same decision can be made from runtime images and predictions
without labels. It would still need independent paired reciprocal validation,
false-fork and edge guards, and the submission protocol in `AGENTS.md`.

The bundle is local at `work/exp239_source_division_fn_taxonomy_20260927/bundle`.
Its manifest SHA256 and exact later launch command are to be recorded after
local sealing and root review. The dedicated future output path is
`runs/exp239_source_division_fn_taxonomy_v1_20260927/output` on nsu-quadro;
it must be absent before any run.
