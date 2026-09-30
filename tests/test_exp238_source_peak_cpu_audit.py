"""EXP238 preregistered source-peak classification and prelabel safety tests."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "work/exp238_source_peak_cpu_audit_20260927/audit_exp238_source_peaks.py"
spec = importlib.util.spec_from_file_location("exp238_source_peak_cpu_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(audit)


def test_missing_endpoint_edges_and_distinct_nodes_are_separate_denominators():
    edges = {(1, 2), (2, 3), (4, 5), (6, 7)}
    endpoint, missed = audit.classify_missing_edges(edges, {3, 4, 5, 6, 7}, {(4, 5)})
    assert len(endpoint) == 2
    assert missed == {1, 2}
    assert sum(all(node in {2} for node in row[2]) for row in endpoint) == 1
    assert sum(all(node in {1, 2} for node in row[2]) for row in endpoint) == 2


def test_offgraph_and_gt_radius_use_original_pixel_scale_and_same_frame():
    peaks = np.array([(0, 0, 0, 10, 0.1), (0, 0, 0, 20, 0.2),
                      (1, 0, 0, 10, 0.3)], dtype=audit.PEAK_DTYPE)
    # A graph node at x=40 suppresses only the first time-0 peak. Time-1
    # reuses the same location and remains off graph.
    graph = {99: (0, 0, 0, 40)}
    gt = {1: (0, 0, 0, 80), 2: (1, 0, 0, 40), 3: (0, 0, 0, 40)}
    qualified, offgraph = audit.qualifying_nodes(peaks, graph, gt, {1, 2, 3})
    assert offgraph == 2
    assert qualified == {1, 2}


def test_distance_boundary_and_outside():
    peaks = np.array([(0, 0, 0, 10, 0.1)], dtype=audit.PEAK_DTYPE)
    # Candidate x=40 pixels. Exactly 7 um is inside; one pixel beyond is out.
    distance_pixels = 7 / audit.SCALE[2]
    gt = {1: (0, 0, 0, 40 + distance_pixels),
          2: (0, 0, 0, 41 + distance_pixels)}
    qualified, offgraph = audit.qualifying_nodes(peaks, {}, gt, {1, 2})
    assert offgraph == 1 and qualified == {1}


def test_raw_pixel_conversion_matches_byte_pinned_horaz_engine():
    parent_engine = ROOT / "work/exp238_source_peak_cache_local_20260927/base/engine.py"
    assert audit.sha(parent_engine) == (
        "4db02fd767ee0e55e4a1ee902fb6ebc2d8683e07c0fe424ee85f7ef906c6dc44")
    code = parent_engine.read_text()
    assert "downsample_array = np.asarray(model_config.downsample, dtype=np.float32)" in code
    assert "coords[:, 1:] *= downsample_array" in code
    assert np.array_equal(audit.DOWNSAMPLE, [1, 4, 4])


def test_dynamic_receipts_are_fail_closed_and_geff_allowlist_is_exact():
    for value in (None, "", "0" * 63, "pending", "G" * 64):
        with pytest.raises(ValueError):
            audit.pinned_hash(value)
    state = {"source_labels_open": False}
    hook = audit.deny_unsealed_geff({"44b6_996155de"}, state)
    allowed = audit.DATA / "44b6_996155de.geff" / "nodes.json"
    other = audit.DATA / "6bba_372c8cb8.geff" / "nodes.json"
    with pytest.raises(PermissionError):
        hook("open", (str(allowed),))
    state["source_labels_open"] = True
    hook("open", (str(allowed),))
    with pytest.raises(PermissionError):
        hook("open", (str(other),))


def test_exact19_config_and_sparse_metadata_contract():
    config = json.loads((SCRIPT.parent / "config.json").read_text())
    ids = audit.exact_ids(config)
    assert len(ids) == 19 and len(set(ids)) == 19
    assert all(audit.pinned_hash(row[key]) for row in config["cohorts"] for key in
               ("status_sha256", "exit_sha256", "complete_sha256",
                "control_sha256", "independent_receipt_sha256"))
    assert audit.pinned_hash(config["cohorts"][0]["independent_receipt_sha256"])
    assert audit.pinned_hash(config["cohorts"][0]["guarded_recheck_receipt_sha256"])
    assert audit.pinned_hash(config["cohorts"][0]["optimization_correction_receipt_sha256"])
    values = np.array([(0, 1, 2, 3, 0.10000000149)], dtype=audit.PEAK_DTYPE)
    frames = [{"t": time, "count": int(time == 0), "floor": 0.075,
               "downsample_zyx": [1, 4, 4], "logit_shape_zyx": [64, 64, 64],
               "selected_threshold": 0.96875, "adaptive_mode": False,
               "tta": True, "gamma": 1.0, "pool_kernel_zyx": [3, 3, 3]}
              for time in range(100)]
    metadata = {"dataset": ids[0], "floor": 0.075, "peak_count": 1,
                "peak_payload_bytes": 12, "peak_dtype": audit.PEAK_DTYPE.descr,
                "frames": frames, "source_labels_read": False,
                "target_data_opened": False}
    audit.check_peak_metadata(metadata, values, ids[0])
    metadata["frames"][0]["downsample_zyx"] = [1, 2, 2]
    with pytest.raises(AssertionError):
        audit.check_peak_metadata(metadata, values, ids[0])


def test_four_gates_are_independent_at_exact_40_percent():
    rows = []
    for experiment, count, edges in (("EXP227", 8, 153), ("EXP236", 11, 514)):
        for index in range(count):
            rows.append({"experiment": experiment, "endpoint_fn_edges": edges if index == 0 else 0,
                         "recoverable_endpoint_fn_edges": (62 if experiment == "EXP227" else 206)
                         if index == 0 else 0,
                         "distinct_missed_endpoint_nodes": 10 if index == 0 else 0,
                         "qualified_distinct_missed_nodes": 4 if index == 0 else 0})
    summaries = audit.summarize(rows)
    assert all(row["edge_gate_40pct"] and row["node_gate_40pct"] for row in summaries)
    rows[0]["qualified_distinct_missed_nodes"] = 3
    summaries = audit.summarize(rows)
    assert summaries[0]["edge_gate_40pct"] is True
    assert summaries[0]["node_gate_40pct"] is False


def test_local_stage_launch_review_and_optimized_mode_guard():
    for script in (ROOT / "scripts/stage_exp238_source_peak_cpu_audit.py",
                   ROOT / "scripts/launch_exp238_source_peak_cpu_audit.py"):
        review = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        result = json.loads(review.stdout)
        assert result["remote_mutation"] is False
        optimized = subprocess.run([sys.executable, "-O", str(script)], cwd=ROOT,
                                   capture_output=True, text=True)
        assert optimized.returncode != 0
        assert "PYTHONOPTIMIZE must be 0" in optimized.stderr


def test_cpu_wrapper_forces_unoptimized_bounded_source_only_process():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import launch_exp238_source_peak_cpu_audit as launcher
        wrapper = launcher.wrapper_source("a" * 64)
    finally:
        sys.path.pop(0)
    compile(wrapper, "exp238_test_wrapper", "exec")
    assert "PYTHONOPTIMIZE='0'" in wrapper
    assert "CUDA_VISIBLE_DEVICES=''" in wrapper
    assert "if not __debug__" in wrapper
    assert "resource.setrlimit(resource.RLIMIT_CPU" in wrapper


def test_independent_completion_verifier_recounts_fixed_decision():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import verify_exp238_source_peak_cpu_audit as verifier
    finally:
        sys.path.pop(0)
    rows = []
    for experiment, count, edges, passing in (("EXP227", 8, 153, 62),
                                              ("EXP236", 11, 514, 205)):
        for index in range(count):
            rows.append({"dataset": f"{experiment}_{index}", "experiment": experiment,
                         "endpoint_fn_edges": edges if index == 0 else 0,
                         "recoverable_endpoint_fn_edges": passing if index == 0 else 0,
                         "distinct_missed_endpoint_nodes": 10 if index == 0 else 0,
                         "qualified_distinct_missed_nodes": 4 if index == 0 else 0,
                         "peak_count": 20, "offgraph_peak_count": 10})
    summaries, decision = verifier.recount(rows)
    assert summaries[0]["edge_gate_40pct"] is True
    assert summaries[1]["edge_gate_40pct"] is False
    assert decision == "REJECT_TRACK_SEEDED_REDETECTION"
    rows[8]["recoverable_endpoint_fn_edges"] = 206
    _, decision = verifier.recount(rows)
    assert decision == "SUPPORT_TRACK_SEEDED_REDETECTION"


def test_independent_verifier_is_local_review_until_cpu_completion():
    script = ROOT / "scripts/verify_exp238_source_peak_cpu_audit.py"
    review = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    assert json.loads(review.stdout)["remote_read"] is False
    optimized = subprocess.run([sys.executable, "-O", str(script)], cwd=ROOT,
                               capture_output=True, text=True)
    assert optimized.returncode != 0
    assert "PYTHONOPTIMIZE must be 0" in optimized.stderr
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import verify_exp238_source_peak_cpu_audit as verifier
    finally:
        sys.path.pop(0)
    source = verifier.remote_source("a" * 64, {"status": "synthetic"})
    compile(source, "synthetic_exp238_remote_verifier", "exec")
    assert "state['geff_open']=True" in source
    assert source.index("assert result['no_label_gate_sha256']") < source.index("state['geff_open']=True")
