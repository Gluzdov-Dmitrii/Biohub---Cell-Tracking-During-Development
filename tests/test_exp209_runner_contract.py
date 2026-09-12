from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runner_keeps_metrics_closed_until_all_eight_gate():
    source = (ROOT / "scripts" / "run_exp209_selected_centroid_confirmation.sh").read_text(encoding="utf-8")
    assert source.count("--radius 3,5,5") == 1
    assert source.count("--radius 2,3,3") == 1
    assert "for number in 00 01 02 03 04" in source
    assert "for number in 00 01 02" in source
    gate = source.index('"$python_bin" "$code/validate_exp209_selected_centroid_chunks_no_metrics.py"')
    merge = source.index('"$python_bin" "$code/merge_exp192_chunk_results.py" "${forward_inputs')
    assembly = source.index('"$python_bin" "$code/build_exp209_selected_centroid_confirmation.py"')
    assert gate < merge < assembly
    assert "base_raw_candidate_cache" in source
    assert '[[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]' in source
    assert "SHA256SUMS.tmp" in source
    assert "cd \"$results\"" in source


def test_launcher_is_atomic_cpu_only_and_pins_runner():
    source = (ROOT / "scripts" / "launch_exp209_remote.sh").read_text(encoding="utf-8")
    assert 'mkdir "$run"' in source
    assert "launch_authorization.txt" in source
    assert "launch_receipt.txt" in source
    assert 'pgrep -af "[r]un_exp209_selected_centroid_confirmation.sh' in source
    assert 'CUDA_VISIBLE_DEVICES="" nohup taskset -c 0-7 bash "$runner"' in source
    assert "bbe7588cb572ce070de328521ddc53cbb18fb917d3e2b10398b93c635a8d0413" in source
