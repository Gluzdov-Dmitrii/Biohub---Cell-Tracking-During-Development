# EXP227 staged Horaz loader CPU microbenchmark — 2026-09-27

The exact immutable EXP227 block02 `FrameWindowDataset.__getitem__` was executed on nsu-quadro CPU 24–27 with CUDA hidden, `num_workers=0`, augmentation disabled, and two source44 movies from the SHA-pinned source manifest. The runner's training batch size is 4; this microbenchmark fetches individual samples because it isolates the dataset loader. No target6bba data, GPU, training, active run or Kaggle POST was touched.

| Access path | 36-window pass A (s) | Reverse-order pass B (s) | Median ms/window |
| --- | ---: | ---: | ---: |
| Staged Zarr open per sample | 0.852 | 0.822 | 23.3 |
| Cached Zarr group per movie | 1.007 | 0.760 | 24.5 |
| Preloaded downsampled uint16 frames | 0.020 | 0.017 | 0.5 |

On this fixed, warmed sequence, cached Zarr handles showed no consistent gain (one pass slower, one faster; median throughput ratio 0.95×). Preloaded access took 45.11× less measured per-sample time than staged opening, with setup excluded from the timed passes. Two movies had [99, 88] valid windows; the 36-index sequence covered 18 unique windows and repeated them. Every returned field, including half-precision image tensors, coordinates, masks, targets and metadata, matched bitwise at every index. All three image-sequence SHA256 values are `146dc94c5065f7c7034312bf3447215386b15b8f3a59f9dea6f2df6b822a0a61`.

Cached group setup took 0.003 s; preloading all 100.0 MiB of downsampled uint16 frames took 1.026 s. For one 36-window pass, preload setup plus median access was 1.045 s versus 0.837 s for baseline; reuse is needed to amortize setup. Process RSS was 415.5 MiB before setup, 415.5 MiB after cached opens, and 716.2 MiB after preload. Peak RSS after benchmark was 779.3 MiB.

This measures only two sparse source movies (maximum two graph nodes per window), repeated windows, and warmed storage/cache. It excludes augmentation, batch collation, training and GPU compute. The observed ratios are a loader optimization lead, not a full-epoch speedup or an OOF quality change. A later implementation should account for per-movie preload memory across all 63/115 source movies and keep the exact dataflow/equality gates.

Evidence: `reports/exp227_horaz_loader_benchmark_20260927.json`; source snapshots: `work/horaz_development_20260922/exp227/loader_benchmark_snapshot_20260927/`. Stage manifest SHA256 `c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26`; exact staged loader SHA256 `063fc77e333d615bbb640f8e8062972cca0e25c3c26a95dbf675137263e7b0b3`.
