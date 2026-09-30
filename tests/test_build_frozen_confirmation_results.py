from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_frozen_confirmation_results import policy_result, rows


def metric_row(name, tp, fp, fn):
    return {
        "dataset": name,
        "edge_tp": tp,
        "edge_fp": fp,
        "edge_fn": fn,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "num_pred_nodes": 100,
        "node_recall": 1.0,
        "total_node_ratio": 0.0,
        "edge_jaccard": tp / (tp + fp + fn),
        "adj_edge_jaccard": tp / (tp + fp + fn),
    }


def test_fixed_policy_never_selects_from_scores():
    base_f = [metric_row(f"6bba_{i:08x}.zarr", 5, 5, 5) for i in range(116)]
    sel_f = [metric_row(f"6bba_{i:08x}.zarr", 8, 2, 2) for i in range(116)]
    base_r = [metric_row(f"44b6_{i + 100:08x}.zarr", 5, 5, 5) for i in range(59)]
    sel_r = [metric_row(f"44b6_{i + 100:08x}.zarr", 7, 3, 3) for i in range(59)]
    payload = policy_result(
        "TEST", base_f, base_r, sel_f, sel_r,
        {"forward": "frozen_a", "reverse": "frozen_b"}, {},
    )
    assert payload["directions"]["forward"]["frozen_arm"] == "frozen_a"
    assert payload["directions"]["reverse"]["frozen_arm"] == "frozen_b"
    assert payload["combined"]["delta"] > 0


def test_rows_rejects_public_twin():
    payload = {"per_movie_by_arm": {"x": [metric_row("6bba_05b6850b.zarr", 1, 0, 0)]}}
    try:
        rows(payload, "x", "6bba", 1)
    except ValueError as exc:
        assert "public twin" in str(exc)
    else:
        raise AssertionError("public twin was accepted")
