from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_exp207_runner_keeps_two_compute_matched_feature_arms() -> None:
    source = (ROOT / "scripts" / "run_exp207_d4_feature_tta8.sh").read_text(encoding="utf-8")
    assert source.count("run_inference off 0 forward") == 1
    assert source.count("run_inference on 1 forward") == 1
    assert source.count("run_inference off 0 reverse") == 1
    assert source.count("run_inference on 1 reverse") == 1
    assert "BIOHUB_EDGE_FEATURE_TTA=\"$feature\"" in source
    assert '[[ "$label" == "off" && "$feature" == "0" || "$label" == "on" && "$feature" == "1" ]]' in source
    assert 'find "$gpu/tracking_repo" -type d -name __pycache__ -prune -exec rm -rf -- {} +' in source
    assert "--det-threshold 0.985 --edge-threshold 0.02 --weak-probability-weight 0.1" in source
    assert "--minimum-length 8 --probability-weight 0.1" in source
    assert "--minimum-length 3 --probability-weight 0.1" in source
    assert source.index("feature_controls.json") < source.index("feature_comparison.json")
    assert "exp192_confirm_" not in source


def test_exp207_launcher_pins_runner_and_is_single_launch() -> None:
    source = (ROOT / "scripts" / "launch_exp207_remote.sh").read_text(encoding="utf-8")
    assert "384ed4551c4455ff42deccf28098cd9906eb29367bb658b2bf4750a55cc567b9" in source
    assert "gpu_launch_receipt.txt" in source
    assert ".gpu-launch-lock" in source
    assert "pgrep -af" in source
    assert "CUDA_VISIBLE_DEVICES" in source
