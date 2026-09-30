"""CPU-only post hoc source8 attribution on sealed EXP227 epoch10 graphs."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys


REMOTE = Path("/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development")
INFERENCE_RUN = REMOTE / "runs/exp227_source_graph10_v1_20260927"
SCORER_CODE = REMOTE / "code/exp227_source_graph10_scorer_v1_20260927"
SCORER_RUN = REMOTE / "runs/exp227_source_graph10_official_v1_20260927"
DATA = REMOTE / "data/exp213_source_view_20260912"
SCORER_MANIFEST_SHA = "9eb0172ad130c693c7c58fd528fdc14c64736cacb9c237158d3ca17221092731"
SCORE_CONFIG_SHA = "23c3a19577abddb171332dd3a8354953190098cf90e25f143d6c4874149d173c"
GRAPH_STATUS_SHA = "d445f1858ca5efe9561667a6e21362d753f047bb5bd7d507c209f076193cde7d"
SCORE_RESULT_SHA = "b9b2eacc8995bbcfb405a636698bc4e1be00cc4d2ae8d18b6231d66a7d18f0d4"
SCORE_GATE_SHA = "949ed2f7ea1af9c18772650ae67e30917c8d934cdcd6e7ab0bf381c6a0a4f343"
SOURCE_SCORE = 0.8114014924249717
SOURCE_IDS = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
)
# A directory digest covers relative path and SHA256 of every source GEFF file.
PINS = {
    "44b6_996155de": ("ab4abc463eb91ae299eff5fa5a6031e45c5ffc54408cd7dc9613834d4b62b6b7", "fa84776d80133c92d1725dfadf890c85507a31065d45c1df1b5448b0a5f99516", "40d9b02706df6cbe85eee251eb863c8408f8e646c4e00566ae7ad961a2301a7b"),
    "44b6_c50204e0": ("df8d7326de5fd40b8bd6fb2e0fb65c7c937f77ce3495fbb84b550d6f0105aae1", "48921579e0cc78690d462fbfbf1d1dcbcd76651b37a65b11481da8436d43856b", "62ea7080d1e477d81b28263f53aecb911f1801332527f4e2bd323f80d877cc69"),
    "44b6_c96cfa10": ("7e347384b3bf031bef0785b45f23a1734b90a7ae997a05fea1f3068095e0f7e1", "b593331f8130d2422671ce7dcba5622960b63e2d98124eaad3594a18ab720fd4", "5f63c09329563cf53b74f64d283609eab5c88e3d218d90d9c9dab647671b2a13"),
    "44b6_551a5dba": ("57f4f629a43b9f7408a8284dbb0cacee33fa392cec2256b15876df0422c49cd4", "0aee3c19cbc8870a8d39a89fd35777d2351cee45569a48545a4afbbdf6f3cc8f", "da705914c3ae0ec9efb8bdeeb2002a1b850401c83eb7beb71909e21f7e38f00f"),
    "44b6_90724892": ("7292325efcad75ec162fa4dc7983dab6e832fc54dd86c48d4a7024681b456812", "591a4403a73fc06b8c097a660da006de5fff8aae21657501b74a4572cc8e6f60", "b967502dc4e4a563733e4868218f6a10cfb9b3dfbfd48dc6086454ec6f648eb0"),
    "44b6_f28707c6": ("a352d1be2bc94cdcc1ba9dbcdde994ab447141583d2a5c5880f60e148777e8a0", "75256035d6cfe74c6fff7cde45d2fc004c1905ba5444640cafe5c2ec7eff005d", "5b0eee85fbb8e6772ee94a54d481a905107168686c40eb6eafc8f283d5338ade"),
    "44b6_deabac95": ("f4c65f93f3633ae83b6593f53321b037acb4c7e63ec173d7aeaed55d2b6e6657", "8fe11441f695c1aeddd66ee055b39b13b49012e5febbcd6414f161fae3a65c5e", "b024684791fd972bcb4a6acf0c7a0a5deb7516f5551c665a324d4b5bdcf154eb"),
    "44b6_341df25f": ("c1dec0829eed7dd6be49938eb871d32cad07f6b6979e5d6d9fe68a86bba6af3a", "1d9fdb1b8861510af204c7055d10a37f17bff6ea6d7b6bd61d80344f2cf4c236", "225e560d40b936784575b83ff8dfa3700c020e27f75c85c3d61b1e8b8b7b2e3d"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(root: Path) -> tuple[str, int]:
    files = sorted((path for path in root.rglob("*") if path.is_file()),
                   key=lambda path: path.relative_to(root).as_posix())
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" +
                      sha(path).encode() + b"\n")
    return digest.hexdigest(), len(files)


def source_guard(event, args):
    if event not in ("open", "os.listdir", "os.scandir"):
        return
    for raw in args:
        if not isinstance(raw, (str, bytes, os.PathLike)):
            continue
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.startswith("6bba_") for part in path.parts):
            raise PermissionError("EXP227 attribution forbids target6bba")
        geff = [part for part in path.parts if part.endswith(".geff")]
        if geff and any(part not in {name + ".geff" for name in SOURCE_IDS} for part in geff):
            raise PermissionError("EXP227 attribution forbids non-source8 GEFF")
        if geff and not any(path.is_relative_to((DATA / (name + ".geff")).resolve())
                            for name in SOURCE_IDS):
            raise PermissionError("EXP227 attribution requires pinned source GEFF roots")
        if path.is_relative_to(DATA.resolve()):
            zarr = [part for part in path.parts if part.endswith(".zarr")]
            if zarr and any(part not in {name + ".zarr" for name in SOURCE_IDS} for part in zarr):
                raise PermissionError("EXP227 attribution forbids non-source8 images")


def edge_decomposition(pred_edges, gt_edges, pred_to_gt, gt_to_pred):
    gt_edge_set, pred_edge_set = set(gt_edges), set(pred_edges)
    gt_out, gt_in = {}, {}
    for source, target in gt_edge_set:
        gt_out.setdefault(source, set()).add(target)
        gt_in.setdefault(target, set()).add(source)
    result = {key: 0 for key in (
        "edge_tp", "fn_missing_both_endpoints", "fn_missing_source_endpoint",
        "fn_missing_target_endpoint", "fn_both_endpoints_matched_link_missing",
        "fp_both_endpoints_matched_wrong_association", "fp_source_anchor_target_unmatched",
        "fp_target_anchor_source_unmatched", "ignored_pred_edges")}
    for source, target in gt_edge_set:
        pred_source, pred_target = gt_to_pred.get(source), gt_to_pred.get(target)
        if pred_source is None and pred_target is None:
            result["fn_missing_both_endpoints"] += 1
        elif pred_source is None:
            result["fn_missing_source_endpoint"] += 1
        elif pred_target is None:
            result["fn_missing_target_endpoint"] += 1
        elif (pred_source, pred_target) in pred_edge_set:
            result["edge_tp"] += 1
        else:
            result["fn_both_endpoints_matched_link_missing"] += 1
    for pred_source, pred_target in pred_edge_set:
        gt_source, gt_target = pred_to_gt.get(pred_source), pred_to_gt.get(pred_target)
        if gt_source is not None and gt_target is not None and (gt_source, gt_target) in gt_edge_set:
            continue
        source_anchor = gt_source is not None and bool(gt_out.get(gt_source))
        target_anchor = gt_target is not None and bool(gt_in.get(gt_target))
        if not source_anchor and not target_anchor:
            result["ignored_pred_edges"] += 1
        elif gt_source is not None and gt_target is not None:
            result["fp_both_endpoints_matched_wrong_association"] += 1
        elif source_anchor:
            result["fp_source_anchor_target_unmatched"] += 1
        else:
            result["fp_target_anchor_source_unmatched"] += 1
    return result


def partition(row):
    endpoint = sum(row[key] for key in ("fn_missing_both_endpoints",
                                           "fn_missing_source_endpoint",
                                           "fn_missing_target_endpoint"))
    association = row["fn_both_endpoints_matched_link_missing"]
    fp = sum(row[key] for key in ("fp_both_endpoints_matched_wrong_association",
                                     "fp_source_anchor_target_unmatched",
                                     "fp_target_anchor_source_unmatched"))
    return endpoint, association, fp


def optimistic_adjusted_edge(gt_edges, endpoint_fn, node_ratio, alpha=0.1):
    assert gt_edges > 0 and 0 <= endpoint_fn <= gt_edges
    return max(0.0, ((gt_edges - endpoint_fn) / gt_edges) * (1 - alpha * node_ratio))


def graph_edges(graph, td):
    attrs = graph.edge_attrs(attr_keys=[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE,
                                        td.DEFAULT_ATTR_KEYS.EDGE_TARGET])
    return [(int(row[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE]),
             int(row[td.DEFAULT_ATTR_KEYS.EDGE_TARGET])) for row in attrs.iter_rows(named=True)]


def matched_maps(graph, td):
    attrs = graph.node_attrs(attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID,
                                        td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID])
    pred_to_gt = {}
    for row in attrs.iter_rows(named=True):
        value = row[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID]
        if value is not None and int(value) != -1:
            pred_to_gt[int(row[td.DEFAULT_ATTR_KEYS.NODE_ID])] = int(value)
    gt_to_pred = {gt: pred for pred, gt in pred_to_gt.items()}
    assert len(gt_to_pred) == len(pred_to_gt)
    return pred_to_gt, gt_to_pred


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU-only runtime required"
    assert tuple(PINS) == SOURCE_IDS and all(name.startswith("44b6_") for name in SOURCE_IDS)
    sys.addaudithook(source_guard)
    assert sha(SCORER_CODE / "code_manifest.json") == SCORER_MANIFEST_SHA
    assert sha(SCORER_CODE / "score_config.json") == SCORE_CONFIG_SHA
    assert sha(INFERENCE_RUN / "output/status.json") == GRAPH_STATUS_SHA
    assert sha(SCORER_RUN / "output/result.json") == SCORE_RESULT_SHA
    assert sha(SCORER_RUN / "output/no_metric_gate.json") == SCORE_GATE_SHA
    config = json.loads((SCORER_CODE / "score_config.json").read_text())
    assert Path(config["inference_run"]) == INFERENCE_RUN
    assert Path(config["output"]).parent == SCORER_RUN
    assert Path(config["data_dir"]) == DATA
    sys.path.insert(0, str(SCORER_CODE))
    from score_exp227_source_graph10 import gate
    from score_exp223_official import evaluator_pins
    plan, graphs, gate_receipt = gate(config)
    assert tuple(row["dataset"] for row in plan["movies"]) == SOURCE_IDS
    assert json.loads((SCORER_RUN / "output/no_metric_gate.json").read_text()) == gate_receipt
    score_result = json.loads((SCORER_RUN / "output/result.json").read_text())
    assert score_result["status"] == "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    assert abs(score_result["summary"]["score"] - SOURCE_SCORE) < 1e-12
    assert [row["dataset"] for row in score_result["rows"]] == list(SOURCE_IDS)
    input_hashes = []
    for name in SOURCE_IDS:
        csv_path = INFERENCE_RUN / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        geff_path = DATA / (name + ".geff")
        expected_csv, expected_receipt, expected_geff = PINS[name]
        assert sha(csv_path) == expected_csv and sha(receipt_path) == expected_receipt
        actual_geff, file_count = tree_sha(geff_path)
        assert file_count == 21 and actual_geff == expected_geff
        input_hashes.append({"dataset": name, "graph_csv_sha256": expected_csv,
                             "graph_receipt_sha256": expected_receipt,
                             "gt_geff_tree_sha256": expected_geff, "gt_files": file_count})
    official_config = json.loads(Path(config["evaluator_config"]).read_text())
    assert sha(Path(config["evaluator_config"])) == config["evaluator_config_sha256"]
    assert official_config["repo_path"] == config["repo"]
    evaluator_pins(official_config)

    import numpy as np
    import tracksdata as td
    from geff import GeffMetadata
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    rows, optimistic = [], []
    recorded = {row["dataset"]: row for row in score_result["rows"]}
    for name in SOURCE_IDS:
        graph = graphs[name]
        ids = sorted(graph["nodes"])
        index = {node_id: offset for offset, node_id in enumerate(ids)}
        points = np.asarray([graph["nodes"][node_id] for node_id in ids], dtype=float).reshape((-1, 4))
        edges = [(index[source], index[target], 1.0, 0.0) for source, target in graph["edges"]]
        pred_graph = build_graph(points, edges)
        gt = open_dataset(DATA / (name + ".zarr"), require_tracks=True, load_image=False)
        metric = evaluate(pred_graph, gt.tracks, scale=gt.scale)
        recall = node_recall(pred_graph, gt.tracks) if pred_graph.num_nodes() and pred_graph.num_edges() else 0.0
        estimate = (GeffMetadata.read(DATA / (name + ".geff")).extra or {})["estimated_number_of_nodes"]
        row = {"dataset": name, **per_sample_metrics(metric, float(estimate), recall)}
        for key, value in recorded[name].items():
            if key == "dataset":
                continue
            assert (row[key] == value if isinstance(value, int) else
                    math.isclose(row[key], value, rel_tol=0, abs_tol=1e-12)), (name, key, row[key], value)
        pred_to_gt, gt_to_pred = matched_maps(pred_graph, td)
        decomposition = edge_decomposition(graph_edges(pred_graph, td),
                                          graph_edges(gt.tracks, td), pred_to_gt, gt_to_pred)
        endpoint_fn, association_fn, association_fp = partition(decomposition)
        assert decomposition["edge_tp"] == row["edge_tp"]
        assert endpoint_fn + association_fn == row["edge_fn"]
        assert association_fp == row["edge_fp"]
        gt_edge_count = row["edge_tp"] + row["edge_fn"]
        bound = optimistic_adjusted_edge(gt_edge_count, endpoint_fn, row["total_node_ratio"])
        rows.append({"dataset": name, "official": row, "gt_edge_count": gt_edge_count,
                     "gt_node_count": gt.tracks.num_nodes(),
                     "matched_gt_nodes": len(gt_to_pred),
                     "decomposition": decomposition,
                     "endpoint_limited_fn": endpoint_fn,
                     "association_limited_fn": association_fn,
                     "association_fp": association_fp,
                     "optimistic_fixed_node_adjusted_edge": bound})
        optimistic.append((gt_edge_count, bound))
    baseline = summarise([row["official"] for row in rows])
    for key, value in score_result["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), (key, baseline[key], value)
    weight = sum(item[0] for item in optimistic)
    optimistic_adj = sum(w * value for w, value in optimistic) / weight
    totals = {key: sum(row["decomposition"][key] for row in rows)
              for key in rows[0]["decomposition"]}
    endpoint = sum(row["endpoint_limited_fn"] for row in rows)
    association = sum(row["association_limited_fn"] for row in rows)
    association_fp = sum(row["association_fp"] for row in rows)
    assert totals["edge_tp"] == sum(row["official"]["edge_tp"] for row in rows)
    assert endpoint + association == sum(row["official"]["edge_fn"] for row in rows)
    assert association_fp == sum(row["official"]["edge_fp"] for row in rows)
    result = {
        "status": "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION",
        "evidence_class": "post hoc source-inner validation used during training monitoring; diagnostic bound, not target OOF or an achievable policy",
        "source_score": SOURCE_SCORE,
        "baseline_official": baseline,
        "pooled": {"gt_edges": weight, "edge_tp": totals["edge_tp"],
                   "edge_fn": endpoint + association, "edge_fp": association_fp,
                   "endpoint_limited_fn": endpoint,
                   "association_limited_fn": association,
                   "association_fp": association_fp,
                   "division_tp": baseline["division_tp"],
                   "division_fp": baseline["division_fp"],
                   "division_fn": baseline["division_fn"],
                   "mean_node_recall": baseline["node_recall"],
                   "details": totals},
        "optimistic": {
            "fixed_node_adjusted_edge_ceiling": optimistic_adj,
            "official_score_if_division_term_held_observed": optimistic_adj + 0.1 * baseline["division_jaccard"],
            "official_score_with_perfect_division_term": optimistic_adj + 0.1,
            "assumptions": "All GT edges with both endpoints matched become TP, all association FP vanish, endpoint-limited FN and fixed predicted-node count remain; official per-movie node-count penalty and GT-edge weighting retained."},
        "inputs": {"graph_status_sha256": GRAPH_STATUS_SHA,
                   "score_result_sha256": SCORE_RESULT_SHA,
                   "score_gate_sha256": SCORE_GATE_SHA,
                   "score_config_sha256": SCORE_CONFIG_SHA,
                   "scorer_manifest_sha256": SCORER_MANIFEST_SHA,
                   "evaluator_config_sha256": config["evaluator_config_sha256"],
                   "rows": input_hashes},
        "rows": rows,
        "limitations": ["Same eight source44 inner movies were used during training monitoring; not target OOF.",
                        "Perfect association and zero false positive edges may violate graph degree/lineage constraints.",
                        "The score scenarios fix the observed division term or assume a perfect one; association changes can alter division outcomes.",
                        "Fixed predicted nodes and their official matching exclude gains from changed detection or thresholding."],
        "target6bba_access": False,
        "candidate_tuning": False,
    }
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
