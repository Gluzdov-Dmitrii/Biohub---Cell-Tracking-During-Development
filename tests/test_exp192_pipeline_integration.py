import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_exp195_confirmation_result import build as build_exp195
from build_exp201_confirmation_result import build as build_exp201
from build_exp202_composed_confirmation_result import compose as compose_exp202
from build_exp206_centroid_composed_confirmation_result import compose as compose_exp206
from build_frozen_confirmation_results import policy_result, rows
from merge_exp192_chunk_results import merge
from validate_exp192_all_chunks_no_metrics import validate_all
from validate_exp192_chunk_structure import sha256


def metric(name, tp=10, fp=2, fn=3, nodes=20):
    return {
        "dataset": name,
        "edge_tp": tp,
        "edge_fp": fp,
        "edge_fn": fn,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "num_pred_nodes": nodes,
        "node_recall": 0.9,
        "total_node_ratio": 1.0,
        "edge_jaccard": tp / (tp + fp + fn),
        "adj_edge_jaccard": tp / (tp + fp + fn),
    }


def payload(status, arms, telemetry=None):
    return {
        "status": status,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: {"placeholder": len(values)} for arm, values in arms.items()},
        "telemetry": telemetry or [],
    }


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_full_exp192_postprocessing_pipeline(tmp_path):
    runs = tmp_path / "runs"
    chunks = []
    forward_filtered, reverse_filtered, reverse_gap, reverse_gap_filtered = [], [], [], []
    forward_flow, reverse_flow, forward_centroid = [], [], []
    specs = (("forward", [24, 24, 24, 24, 20], "6bba"), ("reverse", [24, 24, 11], "44b6"))
    offsets = {"forward": 0, "reverse": 0}
    for direction, sizes, prefix in specs:
        for number, size in enumerate(sizes):
            label = f"{direction}_{number:02d}"
            run = runs / f"exp192_confirm_{label}_20260911"
            names = [f"{prefix}_{i:04x}.zarr" for i in range(offsets[direction], offsets[direction] + size)]
            offsets[direction] += size
            movies = write(run / "movies.json", {"target_development": names})
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": sha256(movies)})
            raw = [metric(name) for name in names]
            write(run / "results/base_raw.json", payload(
                "PASS_FROZEN_REGISTERED_MODEL_EVALUATION",
                {"registered_hungarian": raw, "registered_weak_hungarian": raw},
            ))
            if direction == "forward":
                selected = [metric(name, tp=11) for name in names]
                flow = [metric(name, tp=12) for name in names]
                flow_path = write(run / "results/local_flow.json", payload(
                    "PASS_CACHED_FIXED_LOCAL_FLOW",
                    {"translation": selected, "fixed_local_flow": flow},
                ))
                forward_flow.append(flow_path)
                centroid_path = write(run / "results/intensity_centroid.json", payload(
                    "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT",
                    {"translation": selected, "intensity_centroid_r2_5_5": [metric(name, tp=13) for name in names]},
                ))
                forward_centroid.append(centroid_path)
                path = write(run / "results/base_filtered.json", payload(
                    "PASS_CACHED_SHORT_TRACK_FAMILY", {"no_filter": raw, "min8": selected}
                ))
                forward_filtered.append(path)
            else:
                base_selected = [metric(name, tp=11) for name in names]
                flow = [metric(name, tp=12) for name in names]
                flow_path = write(run / "results/local_flow.json", payload(
                    "PASS_CACHED_FIXED_LOCAL_FLOW",
                    {"translation": base_selected, "fixed_local_flow": flow},
                ))
                reverse_flow.append(flow_path)
                base_telemetry = [
                    {"dataset": name, "variants": {"min3": {"nodes_removed": 1 if index % 2 == 0 else 3}}}
                    for index, name in enumerate(names)
                ]
                base_path = write(run / "results/base_filtered.json", payload(
                    "PASS_CACHED_SHORT_TRACK_FAMILY",
                    {"no_filter": raw, "min3": base_selected},
                    base_telemetry,
                ))
                gap_selected = [metric(name, tp=12) for name in names]
                gap_telemetry = [
                    {"dataset": name, "deepcenter": {
                        "synthetic_added": 2,
                        "deepcenter_accepted": 1,
                        "deepcenter_checked": 2,
                        "endpoint_pairs_selected": 2,
                    }}
                    for name in names
                ]
                gap_path = write(run / "results/gap.json", payload(
                    "PASS_SYNTHETIC_GAP_EVALUATION",
                    {"registered_hungarian": raw, "synthetic_gap_no_veto": gap_selected, "synthetic_gap_deepcenter": gap_selected},
                    gap_telemetry,
                ))
                filtered_path = write(run / "results/gap_filtered.json", payload(
                    "PASS_CACHED_SELECTED_EDGE_SHORT_TRACKS", {"no_filter": gap_selected, "min6": gap_selected}
                ))
                write(run / "results/gap_cache_reproduction.json", {"status": "PASS_EXACT_CACHED_ARM_REPRODUCTION"})
                reverse_filtered.append(base_path)
                reverse_gap.append(gap_path)
                reverse_gap_filtered.append(filtered_path)
    index_path = write(tmp_path / "chunk_index.json", {"chunks": chunks})
    gate = validate_all(index_path, runs)
    assert gate["status"] == "PASS_EXP192_ALL_CHUNKS_NO_METRICS"

    forward_merged = merge(forward_filtered, 116, "6bba")
    reverse_merged = merge(reverse_filtered, 59, "44b6")
    gap_merged = merge(reverse_gap_filtered, 59, "44b6")
    forward_flow_merged = merge(forward_flow, 116, "6bba")
    reverse_flow_merged = merge(reverse_flow, 59, "44b6")
    forward_centroid_merged = merge(forward_centroid, 116, "6bba")
    forward_path = write(tmp_path / "forward_merged.json", forward_merged)
    reverse_path = write(tmp_path / "reverse_merged.json", reverse_merged)
    gap_path = write(tmp_path / "gap_merged.json", gap_merged)
    forward_flow_path = write(tmp_path / "forward_flow_merged.json", forward_flow_merged)
    reverse_flow_path = write(tmp_path / "reverse_flow_merged.json", reverse_flow_merged)
    forward_base = rows(forward_merged, "no_filter", "6bba", 116)
    reverse_base = rows(reverse_merged, "no_filter", "44b6", 59)
    exp190 = policy_result(
        "EXP190_TEST", forward_base, reverse_base,
        rows(forward_merged, "min8", "6bba", 116),
        rows(reverse_merged, "min3", "44b6", 59),
        {"forward": "base_min8", "reverse": "base_min3"}, {},
    )
    exp191 = policy_result(
        "EXP191_TEST", forward_base, reverse_base,
        rows(forward_merged, "min8", "6bba", 116),
        rows(gap_merged, "min6", "44b6", 59),
        {"forward": "base_min8", "reverse": "gap_g45_t20_min6"}, {},
    )
    assert exp190["combined"]["frozen_selected"]["n"] == 175
    assert exp191["combined"]["frozen_selected"]["n"] == 175

    repo_root = Path(__file__).resolve().parents[1]
    policy = repo_root / "outputs/research/exp130_official24_private_first/exp195_fixed_reverse_gate/deployable_policy.json"
    exp195 = build_exp195(
        forward_path, reverse_filtered, reverse_gap, reverse_gap_filtered, policy
    )
    assert exp195["combined"]["frozen_selected"]["n"] == 175
    assert exp195["selection_counts"]["forward_base"] == 116
    assert exp195["selection_counts"]["reverse_base"] + exp195["selection_counts"]["reverse_gap"] == 59
    exp201 = build_exp201(forward_flow_path, reverse_flow_path)
    assert exp201["combined"]["frozen_selected"]["n"] == 175
    assert exp201["directions"]["forward"]["frozen_arm"] == "flow_k32_a050_min8"
    exp202 = compose_exp202(exp195, forward_flow_merged)
    assert exp202["combined"]["frozen_selected"]["n"] == 175
    assert exp202["forward_parent_control_maximum_absolute_error"] == 0.0
    exp206 = compose_exp206(exp195, forward_centroid_merged)
    assert exp206["combined"]["frozen_selected"]["n"] == 175
    assert exp206["forward_parent_control_maximum_absolute_error"] == 0.0
    assert exp206["incremental_vs_exp195"]["delta"] > 0
