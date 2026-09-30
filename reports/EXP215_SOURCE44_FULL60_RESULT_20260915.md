# EXP215 Source44 Full60 Result, 15 September 2026

EXP215 source-only full-cache continuation for `source44b6`, seed `2026`,
completed the preregistered `>=60` epoch gate. No target labels, target metrics,
or Kaggle POST were used.

| Chunk | Final Epoch | Best SHA |
|---|---:|---|
| p01 | 28 | `5e513fe537d680ed8e77df041d9f72cb22abe1d8323a2eea85bd689161c617f4` |
| p02 | 42 | `5e513fe537d680ed8e77df041d9f72cb22abe1d8323a2eea85bd689161c617f4` |
| p03 | 57 | `34602d6d38335f9fff2b192dbd87d4a82b02ec2fbff3bd4e88cfa48d3800168d` |
| p04 | 60 | `d7bc45e5151842263e0b008bf152adc26105cf6e76b7722c46fe38a8e79ce3b4` |

Best source-selection score improved from `0.9457744601354854` to
`0.9480773840263902`, a source-only delta of `+0.0023029238909048`. The selected
epoch is `59`; epoch60 completed cleanly but did not replace the best checkpoint.

Receipts:

- Progress: `reports/exp215_full60_source44_training_progress_20260914.json`
- p04 monitor: `reports/exp215_full60_44b6_s2026_p04_monitor_20260914.json`
- p04 operational amendment:
  `reports/exp215_p04_short_chunk_amendment_20260915.json`

Next gate: freeze the `source44b6` full60 primary checkpoint into a comparison
bundle and run target6bba paired inference against the current EXP214 gapfix
90/60 baseline on the same 116 target6bba movies. Do not claim OOF improvement
from this training result alone.
