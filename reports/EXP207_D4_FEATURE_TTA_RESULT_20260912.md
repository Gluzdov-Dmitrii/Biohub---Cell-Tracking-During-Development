# EXP207 D4 detector and feature TTA — 2026-09-12

## Decision

The primary eight-view feature-TTA hypothesis is rejected for the current
scratch-model weak-linker family. It improves the 24-movie development pooled
score by `+0.0005538700`, and both embryo directions plus every LOMO aggregate
are positive, but the preregistered paired bootstrap lower bound is negative:
`[-0.0006214813,+0.0020187849]`. This does not pass the frozen primary gate.

The separately preregistered detector-TTA diagnostic is strong enough to merit
an untouched 175-movie confirmation. Expanding the detector from the existing
four views to all eight D4 views, while keeping identity-view edge features and
the coordinate-only registered policy fixed, gives:

| Comparison | Base | Candidate | Delta | 95% paired bootstrap CI | P(Delta > 0) | Minimum LOMO |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D4 feature TTA | `0.7604184471` | `0.7609723171` | `+0.0005538700` | `[-0.0006214813,+0.0020187849]` | `0.8023` | `+0.0001231147` |
| D4 detector TTA | `0.7485183131` | **`0.7604641105`** | **`+0.0119457974`** | **`[+0.0009265929,+0.0228854648]`** | **`0.9835`** | **`+0.0091216580`** |

Detector-TTA direction deltas are `+0.0147058021` forward and
`+0.0003702260` reverse; neither direction regresses. Candidate directional
scores are `0.7662230010` and `0.7358695122`. This remains development evidence
on 12+12 movies and is not added to the 175-movie frontier yet.

## Controls and attribution

The D4 mechanism was adapted from the open notebook
`reyhanksatria/biohub-cell-tracking-0-946-lb`, while evaluation, controls and
the reciprocal scratch-model protocol are local work. Exact-coordinate
controls pass at zero error for all 24 movies. Feature-on and feature-off use
identical detector coordinates and coordinate-only registered outputs, while
learned edge choices differ on all 24 movies. This isolates the feature-TTA
comparison from detector movement.

Division TP remains zero; EXP207 tests appearance/augmentation robustness, not
division recovery.

## Integrity, resource use and cleanup

EXP207 ran under the common queue on the assigned RTX6000 UUID
`GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba`, parent PID `241019`, Linux start
tick `440311597`. The monitor retained exact identity, all four inference
passes completed, and the parent, children and GPU processes were absent before
the lease was released to `RELEASED/CURRENT`.

The original manifest has one construction defect: `find` observed the
in-progress `SHA256SUMS.tmp`, then the runner renamed that file. The immutable
manifest is preserved. A separately tested fail-closed verifier established
that this is the sole missing entry, verified the other 109 hashes, and proved
exact current-file coverage before metrics were opened. Verifier SHA-256:
`b04a14202b11398eeabea3bcfd0cb3e6d1560548a6ca969fc8349e75421c58d5`.

All 34 compact top-level result files were exported and checked against the
original manifest. Four reproducible raw-candidate caches plus the disposable
tracking repository, about 98 MiB, were then removed. The preserved remote run
is 351 KiB plus a 15 KiB recovery directory and passes a new post-cleanup
manifest whose local and remote SHA-256 is
`f0fddcc5b1e52bbd1c17a7ac5ff1d590264f362dec30c25c6598c7e38a8bda11`.
No Kaggle action occurred.

