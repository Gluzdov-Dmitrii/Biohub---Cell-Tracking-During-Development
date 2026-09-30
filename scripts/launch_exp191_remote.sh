#!/usr/bin/env bash
set -euo pipefail
root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
run="$root/runs/exp191_gap_prune_composition_20260911"
receipt="$run/launch_receipt.txt"
lock="$run/.launch-lock"

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha 9a93702994f84e3510329419cdfec8b3f63eb949e1e0c0623f7fad570466dfc9 "$run/evaluate_synthetic_gap_deepcenter.py"
check_sha d411f0c937f12928e6019993b7ea5c42d2594356ea820ec3b9c06fd9cd3c190e "$run/evaluate_cached_selected_edge_short_tracks.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$run/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$run/evaluate_coordinate_consensus.py"
check_sha 96702ab982561435c8f9765127e3a2ddc0d3b081355a5dd8198345533ae9f6b6 "$run/merge_prefixed_oof_arms.py"
check_sha 7cc7aae36bf51a212505cca6d41c2e90b0f15659e68d5ff9193ddc8ea604145f "$run/select_nested_pooled_arms.py"
check_sha 0c9bdc68c6b1e80d213948262f15fed8844035f5e535a3c02db8e9134f9afcac "$run/select_nested_pooled_synthetic_gap.py"
check_sha 3ca9fc363f98b95f37c4c5d4bcea7eaba351e04cf723685c41d8dc1520be0278 "$run/validate_cached_arm_reproduction.py"
check_sha d5d0c7c4c7597a2fe89d61c18c75b7402fc69508ec94aa16e5131ffa570a4f57 "$run/run_exp191_gap_prune_composition.sh"
check_sha fba30212d81058e263d9db36dfedd1384fea78eb761b8013505752bb0dc4a190 "$run/preregistration.json"
check_sha 2abb44c27318c49518a3eb3c64c6f3978e5bac5ad8a29a79e239b084c6788892 "$root/runs/exp190_extended_short_track_lengths_20260911/results/forward.json"
check_sha 9584a1f7fdf25272bd4975c17ce860242caa46de934ab658776bb00f4ed28e56 "$root/runs/exp190_extended_short_track_lengths_20260911/results/reverse.json"
check_sha ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/44b6/best.pt"
check_sha ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/6bba/best.pt"

python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
"$python_bin" "$run/validate_synthetic_gap_target_inputs.py" \
  --manifest "$root/runs/exp146_scratch_seed_consensus_20260910/all12_6bba.json" \
  --cache-dir "$root/runs/exp152_dense_native_source_selection_20260910/results/forward_target_low_candidate_cache" \
  --key target_development >/dev/null
"$python_bin" "$run/validate_synthetic_gap_target_inputs.py" \
  --manifest "$root/runs/exp146_scratch_seed_consensus_20260910/all12_44b6.json" \
  --cache-dir "$root/runs/exp152_dense_native_source_selection_20260910/results/reverse_target_low_candidate_cache" \
  --key target_development >/dev/null
bash -n "$run/run_exp191_gap_prune_composition.sh"
"$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" --help >/dev/null
"$python_bin" "$run/evaluate_cached_selected_edge_short_tracks.py" --help >/dev/null

if [[ -e "$receipt" || -e "$run/results/nested_selection.json" ]]; then
  echo "EXP191 launch/output receipt already exists" >&2; exit 23
fi
if pgrep -af '[r]un_exp191_gap_prune_composition' >/dev/null; then
  echo "EXP191 process already exists" >&2; exit 24
fi
mkdir "$lock" 2>/dev/null || { echo "EXP191 launch lock already exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$run/run_exp191_gap_prune_composition.sh" "$root" \
  > "$run/exp191.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
