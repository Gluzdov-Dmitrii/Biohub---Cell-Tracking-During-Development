import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp201_confirmation_result import build


def metric(name, tp):
    return {
        "dataset": name,
        "edge_tp": tp,
        "edge_fp": 2,
        "edge_fn": 3,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "num_pred_nodes": 20,
        "node_recall": 0.9,
        "total_node_ratio": 1.0,
        "edge_jaccard": tp / (tp + 5),
        "adj_edge_jaccard": tp / (tp + 5),
    }


def write(path, prefix, count):
    base = [metric(f"{prefix}_{index:04x}.zarr", 10) for index in range(count)]
    candidate = [metric(f"{prefix}_{index:04x}.zarr", 11) for index in range(count)]
    path.write_text(json.dumps({"per_movie_by_arm": {
        "translation": base, "fixed_local_flow": candidate
    }}), encoding="utf-8")
    return path


def test_builds_fixed_policy_without_selection(tmp_path):
    result = build(
        write(tmp_path / "forward.json", "6bba", 3),
        write(tmp_path / "reverse.json", "44b6", 2),
        expected_forward=3,
        expected_reverse=2,
    )
    assert result["status"] == "PASS_FROZEN_CONFIRMATION_ASSEMBLY"
    assert result["combined"]["frozen_selected"]["n"] == 5
    assert result["combined"]["delta"] > 0
    assert result["directions"]["forward"]["frozen_arm"] == "flow_k32_a050_min8"
