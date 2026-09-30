# EXP214 reduced detector-training dataset

The concrete dataset is on the shared NSU filesystem under:

`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/data/`

Use these two directories together:

- `exp214_reduced_xy4_cache_20260912`: 2,889,782,297 bytes including provenance.
- `exp214_portable_metadata_20260912`: 3,554,352 bytes including provenance.

Total: **2,893,336,649 bytes (2.893 GB)**. Original image stores: **85,701,205,857 bytes (85.701 GB)**. The original stores remain unchanged.

This is an input-specific training representation. The public detector already reads every fourth X/Y pixel; storing exactly those uint16 pixels removes spatial samples that this detector never consumed. Temporal reduction keeps registered pairs of consecutive frames, using every fourth source training window plus all annotated division transitions and their nearby windows. Validation windows remain complete. All source movies are represented. Do not treat this as a raw competition Zarr replacement or pass it directly to arbitrary inference code.

The model must use `scripts/exp214_cache_loader.py` through the trainer's `--image-cache` option. Pass the portable metadata directory as `--data-dir`, and the frozen window-selection receipt as `--window-selection`. Missing image frames deliberately raise an error. The original image directory is not required by this training path. DeepCenter has different spatial preprocessing and does not use this detector cache.

The immutable deployed trainer is in `code/exp214_honest_refit_v5_20260912` below the same remote project root. Its local job configurations are `reports/exp214_reduced*_config_20260912.json`; use the common GPU queue and `scripts/launch_exp214_job.py`, rather than launching unreserved jobs directly. Model selection uses only source validation. The four primary models have a fixed 12-epoch budget. The separate 60-epoch control has its own plan and output path.

Construction and verification are reproducible with:

- `scripts/build_exp214_training_cache.py`: exact XY4 cache for all frames.
- `scripts/derive_exp214_reduced_cache.py`: frozen source-window reduction.
- `scripts/build_exp214_metadata_bundle.py`: portable image metadata and labels.
- `scripts/verify_exp214_cache_loader.py`: actual normalized-tensor equivalence checks.

Each stored raw frame was compared with its corresponding original decoded pixels. Twelve representative source windows also matched their actual normalized tensors bit for bit, including a run with the original images absent from the training data view. Full receipts are `exp214_full_cache_manifest_20260912.json`, `exp214_reduced_cache_manifest_20260912.json`, `exp214_cache_loader_verification_20260912.json`, `exp214_portable_loader_verification_20260912.json`, and `exp214_complete_dataset_bytes_20260912.json` in this reports directory.

The 5.303 GB all-frame detector cache preserves all inputs of this specific detector. The additional temporal reduction to 2.893 GB does not have an automatic no-quality-loss guarantee. Its actual tracking CV is tested separately on complete held-out movies with the registered full12/reduced12/reduced60 comparison. Source-validation accuracy is not a substitute for that result.

Local portable archive: outputs/datasets/exp214_reduced_detector_dataset_20260912.tar,2,909,153,280bytes. SHA256:2449c0725e69f6a0261fc012589344765570553a9bfd205885e2026da85c3eba. Full archive/hash/path/type audit passes16,438regular files,2,893,336,649payload bytes,no symlinks. See exp214_local_dataset_archive_20260912.json. Remote transport tar removed after local verification; both original cache directories retained.
