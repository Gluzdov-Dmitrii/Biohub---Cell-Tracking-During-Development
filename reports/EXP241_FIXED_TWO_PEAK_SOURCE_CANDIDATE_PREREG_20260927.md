# EXP241 fixed two-peak continuation — source-only candidate preregistration

Registered after the label-free EXP240 feasibility result and **before** creating
candidate graphs or reading source labels for the candidate score. EXP240's
independent receipt is `reports/exp240_source_two_peak_chain_verified_20260927.json`
SHA256 `68ea60bc71f0dbca5b0c8664515b027a195a73d11a5bd88be18850c72c6dc161`;
remote result SHA256 `696c951c11a68817ee45505c98173f1a9d89e200477016de992d4504425961b2`.
The exact 19 source movies have 835 conflict-free chains in source44 and 358
in source6. This exceeds EXP240's fixed 10/10 feasibility gate in each cohort,
but does not measure quality. This experiment makes **one** candidate, with no
threshold sweep and no reciprocal target access.

## Fixed label-free graph transform

Read the original 19 EXP227/EXP236 source graph CSVs and EXP240 selected-chain
result only after verifying their sealed manifests, receipts, ordered IDs, graph
hashes, peak hashes and no-label gate. Apply exactly EXP240's deterministic
selection; verify every selected chain against the original graph and original
selected-branch peak record. Keep every original node and edge row unchanged in
meaning and order. For each selected seed, sorted by `(seed ID, p1, p2)`, append
two node rows with new unique node IDs starting at original maximum+1, then two
edge rows `seed→p1→p2` with new unique row IDs starting at original maximum+1.
The raw `(t,z,y,x)` of each new node is the selected peak `(t,z,y,x)` multiplied
by `(1,1,4,4)`; its score does not enter the CSV. Retain the exact competition
CSV header and sentinel `-1` fields. Do not delete, redirect, extend, or recurse
from any original or new edge; no new thresholds, score filters or image models.

The expected additions are exactly 1,670 nodes and 1,670 edges across source44,
and 716 nodes and 716 edges across source6. A label-free gate must verify exact
original row preservation, these counts per movie, graph invariants (same
dataset, finite/in-bounds coordinates, unique IDs, indegree≤1, outdegree≤2,
each edge advances exactly one frame), output hashes and exclusive new paths.
It must be durably written before any GEFF/source label access. Build on CPU
only, with CUDA hidden. If the graph gate fails, stop without scoring.

## Paired source-inner score and fixed promotion gate

After the label-free graph gate, evaluate original and candidate graphs against
the same 19 **source-inner training-monitor** GEFF trees using the pinned
current organizer metric commit `075fc5f5a52d11077f9dc2b074644618f26939e2`
and tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, in the
same environment/process. Verify unchanged original GT-tree hashes before and
after. Require the parent per-movie rows and cohort aggregate to replay the
independently verified EXP227/EXP236 source baseline within `1e-12` before
interpreting candidate scores. Pool official sufficient statistics; never
average movie or cohort scores.

Promote to a separately preregistered reciprocal inference test only if **both**
cohorts independently gain at least `+0.005` absolute official score and the
pooled 19-movie score gains at least `+0.005`, with no decline beyond `1e-12`
in adjusted edge Jaccard, node recall or division Jaccard in either cohort.
Report per-movie and cohort edge TP/FP/FN, division TP/FP/FN, node TP/FP/FN and
recall, and added candidate nodes/edges on annotated frames including their
matched versus unmatched counts. Report the baseline and candidate score even
if the gate fails. A failure stops this fixed additive-repair family; no
retuning on these source labels. A pass is only source development evidence,
not honest reciprocal OOF or a Kaggle submission candidate.

No target GEFF/labels, target inference, GPU lease, Kaggle kernel push or
competition POST is authorized by EXP241. Historical target-label exposure in
the overall research process remains; local honest OOF 0.9+ is unachieved.
