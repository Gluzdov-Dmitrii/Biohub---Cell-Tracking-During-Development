# Grok physical/DL hybrid proposal review — 2026-09-21

Delegated exact saved Cursor Grok4.6ExtraHigh session; completed work/cursor/biohub_hybrid_spec_20260921/result.md. User explicitly deleted timer; no scheduled followups, already running cluster jobs retain bounded safety supervision.

Accepted first mechanism: compare physical association with existing DL associations on the exact same frozen source-validation node set. This isolates conditional association behavior, not raw detector recall and not an end-to-end causal detector comparison. CPU budget<=2h only after provenance/cache and graph gates. No hybrid calculation launched in this turn.

Corrections required before implementation:
- Grok assumes an EXP214 production node cache suitable for source8; that is not established. Audit source exclusion of ALL contributing models. Newly completed EXP221 control13 source8 graph is a possible explicitly preregistered parent; do not silently substitute it. Domain23 must not be selected based on source score for this comparison.
- Final nodes were already selected by the original graph; this induces conditioning bias. Report it. Immutable finalCSV avoids ambiguous overwritten rawTTA caches, but raw candidate recovery is a separate experiment.
- Gap closure must emit legal consecutive-frame edges via supported interpolated nodes; arbitrary skip edges are forbidden. If insertion changes node set, either disable that stage in both arms or report a separate repair arm rather than claiming fixed-node equivalence.
- Physical distance and learned edge cost have different units; Grok min(distance, learned_cost) is invalid without a source-calibrated common cost scale. Its0.5fallback threshold is an unvalidated hypothesis, not an established confidence rule.
- Classical divisions are disabled by configuration; preserve explicit handling and report division loss. Do not infer constraints just from0divisionTP.
- Tiny source-score superiority is not sufficient robust promotion by itself; retain week-plan practicality/stability checks and evaluate any later target once after freezing protocol. Sparse unknown nodes are not automatic negatives.

Source8 results now known: control0.8080132099/domain0.8085925666 (+0.000579); this is not overall175CV. Next user ping: inspect Horaz00 completion/release; continue sealed unlaunched chunks with fresh leases, then validate source-only cache for hybrid experiment. No timer recreation.
