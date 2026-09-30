# Community pooled-OOF update — 2026-09-12

Current Kaggle discussion search still found no numerical pooled OOF result
with enough information about embryo split, checkpoint selection, movie set and
pooling to compare with our reciprocal 175-movie protocol. The only recent
quantitative CV comment says results can vary by roughly
`0.01-0.03` while smarter linkers barely move public LB, but it provides no
pooled score or split definition and is not a benchmark for our frontier:
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739685

Two methodological leads are relevant:

- A participant suggests segment-derived appearance features because point
  detections lose information useful for association. This supports testing
  the already-preregistered EXP207 feature-TTA arm, not treating the comment as
  validation evidence.
- The public CC0 synthetic-data discussion reports 2,174 sequences,
  4,056,226 nodes and 165,267 divisions, compared with only about 304 real
  annotated divisions. This source was already audited locally for EXP024;
  its division prior is highly inflated, so any learned division mechanism/model
  requires real reciprocal fine-tuning and OOF validation:
  https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/732103

Conclusion: `0.6784542971` remains our only comparable confirmed pooled OOF
frontier. Community material contributes mechanism hypotheses, not a target
number.
