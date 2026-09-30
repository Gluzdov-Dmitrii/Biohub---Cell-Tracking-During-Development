# EXP240 source-only two-peak chain feasibility — preregistration

Registered after independently verified EXP238 source-only proposal audit and before any EXP240 graph/peak enumeration, new candidate graph or new source-label score. EXP238 verified receipt: `reports/exp238_source_peak_cpu_audit_verified_20260927.json` SHA256 `04cdb945f1b955ea2960b819706ea03a9c1c0a37f8ed4715052035f37111b3af`. This screen is **label-free**, CPU-only, and uses exactly the 8 EXP227 source44 and 11 EXP236 source6 frozen graph/cache pairs sealed by EXP238. It does not change EXP238's conclusion and does not authorize a Kaggle POST.

## Why this topology

EXP238 found off-graph peaks near 69/153 and 244/514 endpoint-limited source FN edges, but did not show that a valid graph can attach them. The earlier one-frame rescue required two matched, still-free endpoints and had zero feasible source44 cases among 20 anchor-supported missed nodes. This screen instead measures **two consecutive off-graph peaks following an original free track end**, without requiring a future endpoint. It does not claim to repair occupied association edges. The bounded external design review is `work/cursor/exp238-repair-design-20260927-1/result.md`; parent correction `parent_review.md` records that any direct `dt>1` edge in its pseudocode violates the frozen validator's `target.t == source.t+1` rule. EXP240 requires only consecutive-frame edges.

## Exact screen, fixed before enumeration

For each movie, read only the frozen original graph CSV and EXP238 sparse selected-branch peak NPY/metadata. Verify both independent EXP238 cache receipts, the source44 guarded recheck, exact ordered 19 IDs, original parent graph CSV hashes, NPY/metadata hashes, dtype, score floor, scale, and source-only status before any enumeration. Install a deny-all `.geff` audit hook. No source or reciprocal target labels, scores, or metrics may be opened.

Use physical coordinates in µm: graph raw `(z,y,x)` times `(1.625,0.40625,0.40625)`; peak low-resolution `(z,y,x)` times `(1,4,4)` then the same physical scale. A seed is an **original** graph node at frame `t ≤ 97`, with exactly one incoming edge from frame `t−1` and no outgoing edge. Its one-step velocity is `v = x(seed) − x(predecessor)` in µm. A peak is eligible only if its stored probability is **strictly >0.075**, all coordinates are finite/in bounds, and no original graph node in the same frame is within or equal to 7 µm. A legal two-peak chain has distinct peaks `p1` at `t+1` and `p2` at `t+2` with:

- `||p1 − (x(seed)+v)|| ≤ 7 µm`;
- `||p2 − (x(seed)+2v)|| ≤ 7 µm`;
- `||p2 − p1|| ≤ 7 µm`;
- `||(p2−p1) − v|| ≤ 7 µm`.

Count all legal pairs, and count each distinct seed once if it has at least one pair. For a later candidate, a seed's best pair would be selected deterministically by `(sum of four squared residuals, −p1.probability−p2.probability, p1(t,z,y,x), p2(t,z,y,x), seed ID)`, followed by a global greedy conflict pass that uses each peak at most once, never changes/deletes original nodes or edges, creates exactly two new nodes and edges `seed→p1→p2`, and does not recurse on new endpoints. **This screen creates no graph**; the candidate rule is recorded now so raw counts cannot drive a threshold sweep. The only new tunables would require a separate preregistration before a candidate score.

## Fixed decision and follow-up

Report per movie/cohort: original nodes/edges, seed count, off-graph peak count, legal pair count, distinct legal seed count, and selected conflict-free chain count under the deterministic rule. Verify the count/arithmetic and selection without opening labels. If either cohort has **fewer than 10 distinct legal seeds** or **fewer than 10 conflict-free chains**, reject this additive free-terminus repair before source scoring and move effort to embryo-held-out model training. Otherwise permit exactly one derived CPU source graph candidate with this fixed rule; its source-inner paired score gate must be separately recorded before score access and must demand meaningful gain on **both** cohorts without edge, node-recall or division regression and with reported annotated-frame false positives. A feasibility PASS is not a source score, reciprocal OOF gain, or a submission candidate. If the fixed candidate fails its source gate, stop this repair family rather than retune thresholds against the same labels.

No target inference, target GEFF, new GPU lease, or Kaggle POST is authorized by this screen. The latest reciprocal development score remains 0.7488419428/175, historically target-label exposed; historical honest-pedigree EXP209 remains 0.6815218333/175. Local honest OOF 0.9+ is not achieved.
