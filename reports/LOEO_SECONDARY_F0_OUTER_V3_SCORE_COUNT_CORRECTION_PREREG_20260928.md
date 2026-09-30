# Secondary full fold0 one-movie outer v3 — locked graph count correction

Written 2026-09-28 Asia/Novosibirsk before successor implementation. Sealed
local-only v2 template manifest SHA256
`57891c0c6eec1899bc2094d19379ba35b0a04620b2089dcef96721351695a9fb`
passed 20 synthetic tests but is **rejected for real scoring** by independent
review. Keep v2 unchanged. Its exact full-training and release audit gates,
source-only parent/checkpoint/config binding, fixed source44-to-outer-6bba
target `6bba_32db13fc`, image-only graph lock before label read, and metric
component recomputation were reviewed without another deterministic blocker.

The P1 gap is in `score_audit.py`: a coherent result with locked predicted
graph `edges=9, divisions=2` passed after claiming `edge_tp=100` or
`division_tp=100`. The actual pinned organizer metric derives TP and FP from
predicted edges and predicted forks, so the count inequalities below are
necessary. V2's transport hashes and scalar recomputation do not enforce
them.

Create a distinct v3 local-only template. Before accepting any score, require
`edge_tp + edge_fp <= locked_graph.edges` and
`division_tp + division_fp <= locked_graph.divisions`, with the existing
nonnegative integer, graph identity and pre-label gates. Reject impossible
counts even if the derived edge/division Jaccard and combined score are
arithmetically consistent. Verify against the exact locked graph that is
rehash-checked from the prediction tree. Keep the selected checkpoint SHA256
`82115428795e51a31a6a44a8fa983c6743ef4d052539b0daccc04db4ffd568ae`
and sibling architecture/config SHA256
`e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`
as real plan inputs, but do not copy or seal them into v3 until the new
template and independent review pass.

Tests must reproduce v2's false acceptances for both edge and division TP,
show v3 rejection of both and corresponding TP+FP overbounds, retain a
positive exact score fixture, and pass the existing 20 behaviors. Rehash
every file in the new template manifest, compile source, and verify no cache
or partial seal. A separate independent read-only review is required before
real plan/seal/stage/launch. No SSH, GPU, target image/GEFF, Kaggle POST, or
OOF score occurs in this correction.
