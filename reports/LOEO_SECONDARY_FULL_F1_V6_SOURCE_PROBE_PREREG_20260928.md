# Secondary full fold1 v6 — source-only preflight probe

Written 2026-09-28 before v6 code or bundle construction. Parent v5 is a
locally sealed, unstaged package: plan SHA256
`bc751688641bfa0ed62d03ed1d0d4b540862612ac5c47424ef7c3042ae3a7a29`,
21-file manifest SHA256
`f4ca8700b825d996cb6e2ee84366050b562778887a764de0a7c028a546021737`,
controller SHA256
`1a1d4845106d08171a1609d91e93739c7a1b679c8969b558a0bb6024d5012622`.
Fresh read-only source preflight observed 128 exact 6bba Zarr/GEFF pairs and
no run or lease. V5's `remote_snapshot` nevertheless calls `glob('*.geff')`
on the shared view and enumerates excluded 44b6 GEFF filenames. This is an
unneeded target-label namespace exposure before source training.

Create a distinct v6 attempt, lease ID/token, remote code/stage/run paths,
plan and manifest. Change only the preflight/stage source snapshot contract:
derive the 128 source IDs from the pinned split, form their 256 explicit
`<id>.zarr` and `<id>.geff` paths, and check each symlink, existence,
resolved filename and approved source parent. No `glob`, `iterdir`, `rglob`,
`os.listdir` or `os.scandir` over the data view or target GEFF directory is
allowed in `remote_snapshot` or its preflight/stage call chain. Report exact
source counts and invalid links; remove the 199-ID Zarr/GEFF namespace
enumeration and missing/extra fields from `assess_preflight`. The immutable
split/catalog hashes still pin all 199 dataset IDs, and the source loader's
runtime access guard remains mandatory. Preflight and stage must not probe
or read any 44b6 GEFF path. Preserve the 28 final-audit checks and their
post-training audit boundary.

Preserve v5 scientific design: fixed 102 fit/26 inner 6bba movies, all 71
44b6 excluded; 9,949/2,443 windows, 50 epochs, seed 20260929, no warm
start, same trainer, selection and quality gates. Preserve every one-shot
queue request/cancel/release intent, reply, verification and supervisor
contract. No training or inference code changes beyond the v6 identity pins.

Local gate before any remote staging: prove v5 parent SHA pins are unchanged;
run the inherited local tests; add a negative executable source snapshot test
that fails on directory enumeration or any 44b6 GEFF probe and confirms all
256 explicit source paths are visited; check valid and missing source-pair
preflight cases; compile Python without cache; read back the exact 21-file
manifest bytes/SHA, plan link and identity; compare v5/v6 code changes
against this narrow diff. Independent second review is required before a
separate stage decision. This work does not request a GPU, stage code, read
target GEFF contents, submit to Kaggle or claim outer OOF.
