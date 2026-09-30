from pathlib import Path


def test_runner_is_detector_only_and_manifest_safe():
    text = (Path(__file__).resolve().parents[1] / "scripts" / "run_exp211_d4_detector_chunk.sh").read_text()
    assert "BIOHUB_EDGE_FEATURE_TTA=0" in text
    assert "BIOHUB_EDGE_FEATURE_TTA=1" not in text
    assert "d4_raw_candidate_cache/*.npz" in text
    assert '"$run"/results/*.json' in text
    assert '"$run"/results/*.log' in text
    assert 'rm -rf -- "$run/tracking_repo"' in text
    assert 'find "$code" "$run"' not in text


def test_launcher_is_single_start_and_identity_aware():
    text = (Path(__file__).resolve().parents[1] / "scripts" / "launch_exp211_d4_detector_chunk_remote.sh").read_text()
    assert "nohup bash" in text
    assert "start_tick=" in text
    assert "launch_receipt.txt" in text
    assert "run_exp211_d4_detector_chunk.sh" in text
    assert "CUDA_VISIBLE_DEVICES" in text
    assert "evaluate_coordinate_consensus.py" in text


def test_cpu_resume_never_repeats_inference_and_is_snapshot_gated():
    text = (Path(__file__).resolve().parents[1] / "scripts" / "resume_exp211_d4_chunk_cpu.sh").read_text()
    assert "FAILED_STAGE_SHA256SUMS" in text
    assert "sha256sum -c" in text
    assert "evaluate_cached_short_track_family.py" in text
    assert "evaluate_registered_model.py" not in text
    assert "CUDA_VISIBLE_DEVICES" not in text
    assert 'rm -rf -- "$run/tracking_repo"' in text
    assert "evaluate_coordinate_consensus.py" in text
