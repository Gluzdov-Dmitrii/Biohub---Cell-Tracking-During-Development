# Secondary full fold1 v6: source-only probe local handoff

Local successor built 2026-09-28 under preregistration
`LOEO_SECONDARY_FULL_F1_V6_SOURCE_PROBE_PREREG_20260928.md` SHA256
`ba694f4f7a012b958b620b50600b56ef0782758c1ed7629d4eedb1e1072521ed`.
Its parent v5 was never staged. Parent plan SHA256
`bc751688641bfa0ed62d03ed1d0d4b540862612ac5c47424ef7c3042ae3a7a29`,
manifest SHA256
`f4ca8700b825d996cb6e2ee84366050b562778887a764de0a7c028a546021737`
and controller SHA256
`1a1d4845106d08171a1609d91e93739c7a1b679c8969b558a0bb6024d5012622`
were rechecked unchanged before sealing v6.

## Sealed local artifacts

- Directory: `work/loeo-secondary-full-f1-v6-20260928/`
- Attempt `f35d1f896224`; lease `loeo-secondary-full-f1-v6-f35d1f896224`.
- `full_plan.json` SHA256 `424cd05da0f0ceb7cbbe026de501f3d49e00f54911d03f3ca6e2cb1cbd181984`.
- `full_bundle/bundle_manifest.json` SHA256 `e60f60ca359ab402622413456f9122ad1bba05b45a6ca5c6d835436de74964fe`.
- `full_control.py` SHA256 `48d5eff492e2cf96ea4543fcd35603a260b543a7c32c496efbe5a7bca6bac001`.
- `audit_completed_full.py` SHA256 `57f4ccec30cac54b13d34b45a7f804eb8b0dd17106728452805324f01384ecaf` (byte-identical to v5).
- `test_full_local.py` SHA256 `56932d668168a3de9f33e9de9c8c3af0d6111f890c97146e48817fbc9666e54a`.

## Change and evidence

`remote_snapshot` now forms 256 explicit paths from the pinned 128 source6bba
IDs and checks only those `.zarr`/`.geff` symlinks, existence, resolved names
and approved parents. Preflight requires 128 valid source Zarr links, 128 valid
source GEFF links, 256 unique resolved targets and no invalid source link.
It no longer enumerates the 199-ID view or probes 44b6 GEFF names. The
immutable split/catalog SHA pins remain, and the post-training auditor's 28
checks remain unchanged. Versioned identity, preregistration and plan/manifest
hashes are the other intentional changes.

`python -B -m unittest discover -s work/loeo-secondary-full-f1-v6-20260928
-p test_full_local.py -q` passed **31/31**. The new executable test traps
`glob`, `rglob`, `iterdir`, `os.listdir` and `os.scandir` on the data view,
fails any 44b6 source probe, and confirms exactly the 256 source names are
visited in both valid and missing-link simulations. Valid simulation returns
128/128 links, 256 unique resolutions and zero invalid; missing simulation
returns 256 invalid. Preflight fixtures accept the valid source set and
reject one missing GEFF. No-cache compilation passed for all 27 Python files.
Exact readback passed every size/SHA in the 21-file bundle manifest and its
plan/prereg links. The only bundle entry changes versus v5 are
`full_contract.py` (identity) and `preregistration.md`; all fixed science
fields, trainer, training entry point, wrapper, supervisor, one-shot
request/release behavior and auditor are unchanged.

This is local static readiness only. Independent second review and a fresh
source-only remote preflight are needed before any separate staging decision.
No SSH, queue request, remote stage, GPU run, target GEFF content read,
Kaggle POST or outer OOF occurred in this v6 preparation.
