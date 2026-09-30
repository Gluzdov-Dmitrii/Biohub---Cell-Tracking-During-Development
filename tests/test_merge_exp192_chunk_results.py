from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from merge_exp192_chunk_results import merge


def row(name):
    return {
        "dataset": name, "edge_tp": 1, "edge_fp": 0, "edge_fn": 0,
        "division_tp": 0, "division_fp": 0, "division_fn": 0,
        "num_pred_nodes": 1, "node_recall": 1.0,
        "total_node_ratio": 0.0, "edge_jaccard": 1.0, "adj_edge_jaccard": 1.0,
    }


def test_merge_preserves_unique_coverage(tmp_path):
    paths = []
    for number, names in enumerate((["6bba_b.zarr"], ["6bba_a.zarr"])):
        path = tmp_path / f"{number}.json"
        path.write_text(__import__("json").dumps({"per_movie_by_arm": {"x": [row(name) for name in names]}}))
        paths.append(path)
    result = merge(paths, 2, "6bba")
    assert [item["dataset"] for item in result["per_movie_by_arm"]["x"]] == [
        "6bba_a.zarr", "6bba_b.zarr"
    ]
