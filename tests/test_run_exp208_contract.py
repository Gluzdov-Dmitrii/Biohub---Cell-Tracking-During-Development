from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_exp208_runner_is_source_selected_and_target_is_single_arm() -> None:
    source = (ROOT / "scripts" / "run_exp208_source_centroid_family.sh").read_text(encoding="utf-8")
    for radius in ("1,3,3", "1,5,5", "2,3,3", "2,5,5", "2,7,7", "3,5,5"):
        assert f'"{radius}"' in source
    assert source.count("source_checkpoint_validation") == 2
    assert source.index("forward_selection.json") < source.index("forward_target.json")
    assert source.index("reverse_selection.json") < source.index("reverse_target.json")
    assert 'forward_target_args=(--radius "$forward_radius")' in source
    assert 'reverse_target_args=(--radius "$reverse_radius")' in source
    assert '[[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]' in source
    assert '[[ -s "$run/launch_authorization.txt" ]]' in source
    assert '[[ ! -e "$results" ]]' in source
    assert 'result["movies"] == 175' in source
    assert 'base[name]["num_pred_nodes"] == selected[name]["num_pred_nodes"]' in source
    assert "exp192_confirm_" not in source


def test_exp208_launcher_is_atomic_cpu_only_and_pins_runner() -> None:
    source = (ROOT / "scripts" / "launch_exp208_remote.sh").read_text(encoding="utf-8")
    assert 'mkdir "$run"' in source
    assert "launch_authorization.txt" in source
    assert "launch_receipt.txt" in source
    assert "pgrep -af" in source
    assert 'CUDA_VISIBLE_DEVICES="" nohup bash "$runner"' in source
    assert "resource=CPU_ONLY" in source
    assert "ce78e9e942cb41dd0cfee9dafce677baca865cb8120f0c65f334f224b87380de" in source
