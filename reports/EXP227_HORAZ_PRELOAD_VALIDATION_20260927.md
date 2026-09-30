# EXP227 Horaz uint16 preload development check — 2026-09-27

An isolated development copy of immutable EXP227 block02 adds an optional `preload_uint16_frames` argument to `FrameWindowDataset` and connects it to both train and validation loaders through `getattr(cfg, "preload_uint16_frames", False)`. The default path keeps per-sample Zarr access. The option stores downsampled uint16 frames, converts only each requested window to float32, and leaves duplicate-frame checks, interpolation, normalization, augmentation, metadata and output fields in the original order. The isolated code manifest SHA256 is `ee77a6b79b0cc349d6968425e7aff1c8d9037e6378efe3d481f21afb3f6ba4d9`; parent stage manifest SHA256 is `c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26`. This copy has not been launched for training.

Source44 training movies `44b6_33b596bf` (sparse) and `44b6_d29c9ab2` (dense) were selected by reading GEFF and image **metadata only** across the pinned 63-movie source manifest. They produced [49, 99] valid windows and maximum 16 nodes/window. All validation ran on nsu-quadro CPU24–27 with CUDA hidden, 32 GiB virtual limit and no target6bba data.

Parity passed: six raw uint16 frames at start/middle/end matched byte for byte; 1728 direct field comparisons across repeated and first/last valid windows passed with augmentation off/on and seeds 0, 3407 and 209. Constructor and augmentation Torch RNG states matched. Two batch4 collations passed (augmentation off/on; 36 field comparisons). A full shuffled, augmented, `num_workers=0` one-pass digest and final RNG state matched among original, new default and preloaded paths across all 148 windows.

| Loader path | Dataset setup (s) | One-pass A (s) | Reverse-order one-pass B (s) | Median one-pass (s) |
| --- | ---: | ---: | ---: | ---: |
| Original staged | 0.007 | 3.465 | 3.810 | 3.638 |
| New default | 0.008 | 3.448 | 3.506 | 3.477 |
| New preloaded | 1.231 | 0.152 | 0.127 | 0.140 |

The preloaded arrays hold 100.0 MiB. RSS was 416.4 MiB before preload, 686.3 MiB after, and peak 904.0 MiB. Median preload setup plus one pass was 1.371 s versus 3.645 s for original. The timed passes include batch collation, shuffle and augmentation; model/GPU compute and all other movies are excluded. These numbers support consideration of a separately registered GPU pilot, not a full-epoch speedup or OOF quality claim.

A separate source44-train metadata-only estimate for all 63 movies is 3.08 GiB of uint16 arrays under the 8 GiB option cap (`reports/exp227_source44_preload_footprint_20260927.json`). Full-source process RSS and GPU training remain unmeasured.

Evidence: `reports/exp227_horaz_preload_validation_20260927.json`; exact source diff: `reports/exp227_horaz_preload_development_20260927.patch`; isolated copy: `work/horaz_development_20260922/exp227/loader_preload_dev_20260927/`.
