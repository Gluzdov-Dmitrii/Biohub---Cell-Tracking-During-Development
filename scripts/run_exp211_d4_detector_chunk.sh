#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
direction="${2:?direction required}"
run="${3:?run path required}"
code="$(cd "$(dirname "$0")" && pwd)"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
data="$root/data/honest195_missing/train"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]
mkdir -p "$run/results" "$run/tracking_repo"

case "$direction" in
  forward)
    repo="$forward_repo"
    weights="$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth"
    minimum=8
    ;;
  reverse)
    repo="$reverse_repo"
    weights="$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth"
    minimum=3
    ;;
  *) echo "direction must be forward or reverse" >&2; exit 2 ;;
esac

cp -a "$repo/src" "$run/tracking_repo/"
cp -a "$repo/scripts" "$run/tracking_repo/"
find "$run/tracking_repo" -type d -name __pycache__ -prune -exec rm -rf -- {} +
cp "$code/exp211_predict_unet_transformer_d4_detector.py" \
  "$run/tracking_repo/scripts/predict_unet_transformer.py"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
BIOHUB_EDGE_FEATURE_TTA=0 "$python_bin" "$code/evaluate_registered_model.py" \
  --repo "$run/tracking_repo" --data-dir "$data" --weights "$weights" \
  --movies-json "$run/movies.json" --movie-key target_development \
  --output "$run/results/d4_raw.json" --det-threshold 0.985 \
  --edge-threshold 0.02 --weak-probability-weight 0.1 --unet-batch-size 4 --seed 314159 \
  > "$run/results/d4_raw.log" 2>&1

"$python_bin" "$code/evaluate_cached_short_track_family.py" \
  --repo "$run/tracking_repo" --data-dir "$data" --movies-json "$run/movies.json" \
  --cache-dir "$run/results/d4_raw_candidate_cache" \
  --minimum-length 1 --minimum-length "$minimum" \
  --output "$run/results/d4_filtered.json" > "$run/results/d4_filtered.log" 2>&1

"$python_bin" "$code/validate_exp211_d4_chunk_structure.py" \
  --run-dir "$run" --direction "$direction" \
  --output "$run/results/structure_validation.json" \
  > "$run/results/structure_validation.log" 2>&1

rm -rf -- "$run/tracking_repo"
sha256sum "$code"/*.py "$code"/*.sh "$run/movies.json" \
  "$run"/results/*.json "$run"/results/*.log \
  "$run"/results/d4_raw_candidate_cache/*.npz > "$run/SHA256SUMS.tmp"
mv "$run/SHA256SUMS.tmp" "$run/SHA256SUMS"
printf 'PASS_EXP211_D4_DETECTOR_CHUNK\n'

