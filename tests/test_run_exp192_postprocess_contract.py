from pathlib import Path


def test_no_metric_gate_precedes_every_merge_and_frozen_builder():
    text = (Path(__file__).resolve().parents[1] / "scripts/run_exp192_postprocess.sh").read_text()
    gate = text.index("validate_exp192_all_chunks_no_metrics.py")
    gate_execution = text.index("validate_exp192_all_chunks_no_metrics.py", gate + 1)
    merge_execution = text.index("merge_exp192_chunk_results.py", text.index("mkdir \"$temporary\""))
    centroid_execution = text.index(
        "evaluate_cached_intensity_centroid_refinement.py", text.index("mkdir \"$temporary\"")
    )
    centroid_gate_execution = text.index(
        "validate_exp206_centroid_chunks_no_metrics.py", centroid_execution
    )
    centroid_merge_execution = text.index(
        '"${forward_centroid[@]}"', centroid_gate_execution
    )
    exp190_execution = text.index("build_frozen_confirmation_results.py", text.index("mkdir \"$temporary\""))
    assert gate_execution < centroid_execution < centroid_gate_execution
    assert centroid_gate_execution < merge_execution <= centroid_merge_execution < exp190_execution
    assert text.index("build_exp195_confirmation_result.py", exp190_execution) < text.index(
        "build_exp202_composed_confirmation_result.py", exp190_execution
    )
    assert "--reference-nested \"$temporary/exp195_confirmation.json\"" in text
    assert "build_exp206_centroid_composed_confirmation_result.py" in text
    assert "exp206_vs_exp195_stability.json" in text
    assert text.rstrip().endswith('echo "PASS_EXP192_FROZEN_POSTPROCESS $final"')
