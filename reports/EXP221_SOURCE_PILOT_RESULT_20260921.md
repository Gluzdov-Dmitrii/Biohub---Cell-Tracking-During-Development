# EXP221: paired source pilot complete

Both arms completed epoch12→24, returncode0, no timeout, target_data_opened=false. Live process identity/group checks show stopped; both leases RELEASED. Same starting model+optimizer SHA and same12post-start epochs verified. Runtime32.83min control,33.94min domain. Source-only metric is accuracy×recall, not official tracking score.

| Source selection statistic | Control | Domain augmentation | Domain minus control |
|---|---:|---:|---:|
| Best post-intervention proxy |0.9366348671 (epoch13)|0.9376560530 (epoch23)|+0.0010211859|
| Fixed final epoch24 proxy |0.9363200158|0.9321096533|-0.0042103624|
| Mean epochs13–24 (descriptive) |0.9298733616|0.9286613539|-0.0012120077|

The original source-selection rule picks best post-intervention checkpoint for both arms; do not switch to final epoch after seeing results. The selected improvement is small and not consistent across these descriptive comparisons. It does not prove robustness or a gain on final graph score, and does not justify more training.

Next bounded gate: evaluate the exact two source-selected checkpoints on unchanged source-validation movies through a frozen graph pipeline, with source-only ancillary model provenance checked. No heldout target6bba label access or tuning. If the source graph gate is not feasible without contamination, preserve checkpoints and prioritize public-weight reproduction instead.

Receipts: `exp221_source_pilot_result_20260921.json`, `exp221_training_live_20260921.json`. Selected SHA control `e4175019c11105ea8b87324f9f787f3b0710d9e4df5862cd2d03ff8204759b5e`; domain `7de53cee104baebd7d7c380bd41b90c55eaa223c8167b9938bf3f76c8be7dea8`. Final SHA and contracts in result JSON. Actual remote checkpoint SHA verification will be repeated before inference load.
