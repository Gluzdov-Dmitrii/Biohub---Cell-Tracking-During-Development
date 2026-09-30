import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_exp192_descriptive_honest195 import build


def row(name, tp):
    return {"dataset": name, "edge_tp": tp, "edge_fp": 1, "edge_fn": 1, "node_tp": tp, "node_fp": 1, "node_fn": 1, "division_tp": 0, "division_fp": 0, "division_fn": 0, "estimated_number_of_nodes": tp + 2, "node_recall": 0.9, "adj_edge_jaccard": 0.5}


def dump(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_builds_exact_195_non_twin_aggregate(tmp_path):
    cf = [row(f"6bba_c{i:03}.zarr", 2) for i in range(116)]
    cr = [row(f"44b6_c{i:03}.zarr", 2) for i in range(59)]
    def confirmation(reverse_arm):
        return {"status": "PASS_FROZEN_CONFIRMATION_ASSEMBLY", "directions": {
            "forward": {"base_rows": cf, "selected_rows": cf, "frozen_arm": "base_min8"},
            "reverse": {"base_rows": cr, "selected_rows": cr, "frozen_arm": reverse_arm},
        }}
    exp190 = dump(tmp_path / "c190.json", confirmation("base_min3"))
    exp191 = dump(tmp_path / "c191.json", confirmation("gap_g45_t20_min6"))
    df_names = [f"6bba_d{i:02}.zarr" for i in range(10)]
    dr_names = [f"44b6_d{i:02}.zarr" for i in range(10)]
    df = dump(tmp_path / "df.json", {"per_movie_by_arm": {"no_filter": [row(x, 1) for x in df_names], "min8": [row(x, 2) for x in df_names]}})
    dr = dump(tmp_path / "dr.json", {"per_movie_by_arm": {"no_filter": [row(x, 1) for x in dr_names], "min3": [row(x, 2) for x in dr_names]}})
    dg = dump(tmp_path / "dg.json", {"per_movie_by_arm": {"gap_primary_min6": [row(x, 3) for x in dr_names]}})
    result = build(exp190, exp191, df, dr, dg)
    assert result["status"] == "PASS_EXP192_DESCRIPTIVE_HONEST195"
    assert result["experiments"]["EXP190"]["combined"]["movie_count"] == 195
    assert result["experiments"]["EXP191"]["directions"]["forward"]["movie_count"] == 126
    assert result["experiments"]["EXP191"]["directions"]["reverse"]["movie_count"] == 69
