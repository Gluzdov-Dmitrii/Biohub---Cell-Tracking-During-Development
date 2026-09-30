# Primary full fold1 v7 — source-only preflight path correction

Written 2026-09-28 before v7 implementation. The sealed v6 full-fold package
is preserved and has never been remotely staged or launched: plan SHA256
`51bff74097e56c42cb9a8b00d1edec80b555e101913f1423cc9c85ffaa9ea224`,
21-file bundle manifest SHA256
`857b712521801d16948c51b32f430bb40f73965a09e4371681e1b8ee4f1ef5f1`.
Its 43 local tests and 21-file readback passed. The separate exact-path
source preflight receipt
`work/loeo-primary-full-f1-v6-preflight-20260928/exact_source_path_preflight.json`
SHA256 `0ad5614ddc72bcd0a3895a9351308f7d514c6e2c4a021dd53ab2da3d1ba75b2c`
checked 256 direct source6bba Zarr/GEFF paths and found no invalid pair.
The scope correction receipt SHA256
`7a323c01c832591e585c6e95e808585e58e56b31956630e545cbdb262f48fbb1`
retracted the no-enumeration description of an earlier wildcard probe.

## Rejected v6 controller behavior

`remote_snapshot()` still computes global `data.glob('*.zarr')` and
`data.glob('*.geff')`, including shared-view target `44b6` entry names, and
`assess_preflight()` requires remote counts/missing/extra sets for all 199
catalog entries. Consequently the controller must not stage v6, even though
the separate direct-path source probe passed. No target GEFF contents were
opened by the v6 preflight; the defect is name enumeration at the controller
stage gate.

## Fixed successor

Create a distinct v7 attempt, plan, code/run/stage paths, lease/token and
manifest. Preserve v6 source-only science and training: pinned 199-ID split
SHA, 102 fit and 26 inner source `6bba` movies, 71 sealed outer `44b6`
IDs, 9,949/2,443 windows, 50 epochs, seed `20260930`, cold start, exact
trainer/selection/quality gate and 28 named final checks. Preserve v6
one-shot queue request, waiting cancel, unlaunched and manual release,
supervisor release claim, raw reply and audit controls.

In v7 `remote_snapshot()`, use only the 128 pinned source `6bba` IDs from
`validate_split()` to form exact `.zarr` and `.geff` paths. Probe those 256
paths directly for symlink existence and ID-preserving resolution within the
two approved source parents. Do not list, glob or otherwise enumerate the
shared-view directory or a target `44b6` GEFF path during controller
preflight or stage. Replace the 199-remote-entry gate with an exact 128
source-pair gate. Retain the 199-ID catalog SHA assertion on the locally
pinned split; that local split validation does not access remote target GEFF.
Fail closed for a missing, foreign, duplicate or malformed source pair.

Local validation must show an explicit negative fixture where a target
GEFF exists but any target path probe or directory enumeration raises, while
v7 remote snapshot and preflight pass for exact source paths. Exercise
missing/foreign source pair failure, all inherited v6 tests, no-cache
compilation, 21-file manifest readback and comparison of unchanged
science/training files. Independent review is required before remote stage.

This preregistration authorizes only local code, plan, tests and manifest.
No SSH, remote stage, queue/GPU action, target image or GEFF read, target
labels, outer score or Kaggle POST is part of this correction.
