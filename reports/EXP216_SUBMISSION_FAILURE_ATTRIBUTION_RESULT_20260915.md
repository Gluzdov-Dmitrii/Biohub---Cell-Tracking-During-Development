# EXP216 Submission Failure Attribution Result, 15 September 2026

EXP216 completed the preregistered read-only decomposition on the frozen EXP214
gapfix90 paired175 submission CSVs. The analyzer verified every shard CSV hash
against the recorded `metrics.json`, rebuilt graphs, ran the official evaluator
matching, and asserted decomposed `edge_tp`, `edge_fn`, and `edge_fp` against the
official and recorded counts. No inference change, threshold choice, Kaggle POST,
or output mutation occurred.

| Arm | Score | Edge FN | Edge FP | Endpoint FN | Association FN | Endpoint FN frac |
|---|---:|---:|---:|---:|---:|---:|
| public | `0.7427291486` | `18003` | `15188` | `10318` | `7685` | `0.573127` |
| local | `0.7132851518` | `21929` | `15003` | `13701` | `8228` | `0.624789` |

## By Embryo

| Arm | Embryo | Edge FN | Edge FP | Endpoint FN | Association FN | Endpoint FN frac |
|---|---|---:|---:|---:|---:|---:|
| public | 44b6 | `1960` | `1649` | `1193` | `767` | `0.608673` |
| public | 6bba | `16043` | `13539` | `9125` | `6918` | `0.568784` |
| local | 44b6 | `1717` | `2029` | `557` | `1160` | `0.324403` |
| local | 6bba | `20212` | `12974` | `13144` | `7068` | `0.650307` |

Top endpoint-limited public movies are concentrated in target6bba:
`6bba_6feb10f0` (`1118/1126` endpoint FN), `6bba_ab78413d` (`730/757`),
`6bba_ebff6e76` (`318/434`), `6bba_78a7bd97` (`294/349`), and
`6bba_57b7cc1e` (`286/460`). Top association-limited public movies also sit in
target6bba, especially `6bba_57b7cc1e`, `6bba_af149c94`, `6bba_6feeb0b1`,
`6bba_786893ac`, `6bba_9a41d029`, and `6bba_5c039895`.

## Interpretation

Endpoint errors are the largest single failure class on the current best public
graph, but association failures remain too large to ignore. The decisive weak
side is still source44b6 -> target6bba: it carries most edge FN and includes the
catastrophic missing-node movies. The target44b6 side has already crossed 0.8 in
the public graph, so the fastest route toward pooled 0.8 is not more source44
epochs or wider layers; EXP217 already showed that full-source continuation
regresses target6bba.

The next local-improvement experiment should therefore be a guarded detector
rescue on target6bba, paired with association/FP safety checks. Do not repeat
coarse count matching from EXP198. Prefer a narrow, source-frozen intervention:
recover plausible short or missing endpoint components only when geometry and/or
independent center evidence support them, then score once against the exact
EXP214 gapfix90 baseline.

## Artifacts

- Result JSON: `outputs/research/exp216_submission_failure_attribution_20260915/gapfix_new90_edge_failure_decomposition.json`
- Result JSON SHA256: `34361b4eefa111e4e886f7bb81e1ba1ccc4a11dd77e092755f99f0d581343e04`
- Stdout SHA256: `b20178eed5290b7943e783cb5bd754f53a5730e2c747bed6cea3d65efec682bf`
- Stderr SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Recorded metrics JSON SHA256: `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5`
