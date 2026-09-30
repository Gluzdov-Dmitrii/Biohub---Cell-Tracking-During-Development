"""Physical GT edge displacement on the sealed EXP227 epoch10 source8 graphs."""

import collections
import gc
import time


def _distribution(values):
    import numpy as np

    if not values:
        return {"count": 0, "min": None, "q25": None, "median": None,
                "q75": None, "max": None}
    array = np.asarray(values, dtype=float)
    assert np.all(np.isfinite(array)) and np.all(array >= 0)
    return {"count": len(values), "min": float(array.min()),
            "q25": float(np.quantile(array, 0.25)),
            "median": float(np.median(array)),
            "q75": float(np.quantile(array, 0.75)), "max": float(array.max())}


def _bins(edges):
    short = [row for row in edges if row["distance_um"] <= 7.0]
    long = [row for row in edges if row["distance_um"] > 7.0]

    def record(group):
        tp = sum(row["class"] == "tp" for row in group)
        return {"gt_edges": len(group), "tp": tp,
                "recall": tp / len(group) if group else None}

    return {"at_most_7um": record(short), "over_7um": record(long)}


def _movie(name, pred, gt, pred_to_gt, gt_to_pred, scale, prior_attr, prior_assoc):
    import numpy as np
    import tracksdata as td

    key = td.DEFAULT_ATTR_KEYS.NODE_ID
    nodes = {int(row[key]): row for row in gt.node_attrs().iter_rows(named=True)}
    gt_edges = set(graph_edges(gt, td))
    pred_edges = set(graph_edges(pred, td))
    xyz_scale = np.asarray(scale, dtype=float)
    assert xyz_scale.shape == (3,) and np.all(np.isfinite(xyz_scale)) and np.all(xyz_scale > 0)
    assert len(gt_edges) == prior_attr["gt_edge_count"]
    assert len(nodes) == prior_attr["gt_node_count"]
    assert len(gt_to_pred) == prior_attr["matched_gt_nodes"]

    cases = []
    association_ids = set()
    for source, target in sorted(gt_edges):
        before, after = nodes[source], nodes[target]
        frame_delta = int(after["t"]) - int(before["t"])
        assert frame_delta > 0
        source_point = np.asarray([float(before[axis]) for axis in ("z", "y", "x")])
        target_point = np.asarray([float(after[axis]) for axis in ("z", "y", "x")])
        distance = float(np.linalg.norm((target_point - source_point) * xyz_scale))
        assert np.isfinite(distance) and distance >= 0
        ps, pt = gt_to_pred.get(source), gt_to_pred.get(target)
        if ps is None or pt is None:
            edge_class = "endpoint_limited_fn"
        elif (ps, pt) in pred_edges:
            edge_class = "tp"
        else:
            edge_class = "association_limited_fn"
            association_ids.add((source, target))
        cases.append({"gt_source_id": source, "gt_target_id": target,
                      "source_t": int(before["t"]), "target_t": int(after["t"]),
                      "frame_delta": frame_delta, "distance_um": distance,
                      "class": edge_class})

    expected_ids = {(row["gt_source_id"], row["gt_target_id"]) for row in prior_assoc}
    assert association_ids == expected_ids, name
    assert len(association_ids) == prior_attr["association_limited_fn"]
    counts = collections.Counter(row["class"] for row in cases)
    assert counts["tp"] == prior_attr["official"]["edge_tp"]
    assert counts["endpoint_limited_fn"] == prior_attr["endpoint_limited_fn"]
    assert counts["association_limited_fn"] == prior_attr["association_limited_fn"]
    assert counts["tp"] + counts["endpoint_limited_fn"] + counts["association_limited_fn"] == len(gt_edges)

    consecutive = [row for row in cases if row["frame_delta"] == 1]
    nonconsecutive = [row for row in cases if row["frame_delta"] != 1]
    summaries = {edge_class: _distribution([row["distance_um"] for row in consecutive
                                            if row["class"] == edge_class])
                 for edge_class in ("tp", "endpoint_limited_fn", "association_limited_fn")}
    bins = _bins(consecutive)
    short, long = bins["at_most_7um"], bins["over_7um"]
    direction = (summaries["association_limited_fn"]["count"] > 0
                 and summaries["tp"]["count"] > 0
                 and summaries["association_limited_fn"]["median"] > summaries["tp"]["median"]
                 and short["gt_edges"] > 0 and long["gt_edges"] > 0
                 and long["recall"] < short["recall"])
    return {"dataset": name, "scale_zyx_um": xyz_scale.tolist(),
            "gt_edges": len(cases), "consecutive_gt_edges": len(consecutive),
            "nonconsecutive_gt_edges": len(nonconsecutive),
            "nonconsecutive_by_class": dict(collections.Counter(
                row["class"] for row in nonconsecutive)),
            "class_counts_all_edges": dict(counts), "displacement_um": summaries,
            "recall_by_distance": bins, "direction_consistent": bool(direction),
            "cases": cases}


def main():
    import numpy as np
    import tracksdata as td
    from geff import GeffMetadata

    started = time.time()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert tuple(PINS) == SOURCE_IDS and all(name.startswith("44b6_") for name in SOURCE_IDS)
    assert PRIOR_ATTR["status"] == "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION"
    assert PRIOR_ATTR["source_score"] == SOURCE_SCORE
    assert PRIOR_ATTR["pooled"]["gt_edges"] == 2039
    assert PRIOR_ATTR["pooled"]["edge_tp"] == 1799
    assert PRIOR_ATTR["pooled"]["endpoint_limited_fn"] == 153
    assert PRIOR_ATTR["pooled"]["association_limited_fn"] == 87
    assert PRIOR_OCCUPIED["status"] == "PASS_EXP227_SOURCE10_OCCUPIED_LINKS"
    assert PRIOR_OCCUPIED["totals"]["association_limited_fn"] == 87
    assert [row["dataset"] for row in PRIOR_ATTR["rows"]] == list(SOURCE_IDS)
    assert [row["dataset"] for row in PRIOR_OCCUPIED["rows"]] == list(SOURCE_IDS)

    sys.addaudithook(source_guard)
    assert sha(SCORER_CODE / "code_manifest.json") == SCORER_MANIFEST_SHA
    assert sha(SCORER_CODE / "score_config.json") == SCORE_CONFIG_SHA
    assert sha(INFERENCE_RUN / "output/status.json") == GRAPH_STATUS_SHA
    assert sha(SCORER_RUN / "output/result.json") == SCORE_RESULT_SHA
    assert sha(SCORER_RUN / "output/no_metric_gate.json") == SCORE_GATE_SHA
    config = json.loads((SCORER_CODE / "score_config.json").read_text())
    assert Path(config["inference_run"]) == INFERENCE_RUN and Path(config["data_dir"]) == DATA
    sys.path.insert(0, str(SCORER_CODE))
    from score_exp227_source_graph10 import gate
    from score_exp223_official import evaluator_pins
    plan, graphs, gate_receipt = gate(config)
    assert tuple(row["dataset"] for row in plan["movies"]) == SOURCE_IDS
    assert json.loads((SCORER_RUN / "output/no_metric_gate.json").read_text()) == gate_receipt
    assert gate_receipt["status"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
    official_config = json.loads(Path(config["evaluator_config"]).read_text())
    assert sha(Path(config["evaluator_config"])) == config["evaluator_config_sha256"]
    assert official_config["repo_path"] == config["repo"]
    evaluator_pins(official_config)
    recorded = json.loads((SCORER_RUN / "output/result.json").read_text())
    assert recorded["status"] == "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    assert math.isclose(recorded["summary"]["score"], SOURCE_SCORE, rel_tol=0, abs_tol=1e-12)
    # All source8 graph/GEFF hashes are checked before any label is opened.
    input_pins = []
    for name in SOURCE_IDS:
        csv_path = INFERENCE_RUN / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        geff_path = DATA / (name + ".geff")
        expected_csv, expected_receipt, expected_geff = PINS[name]
        assert sha(csv_path) == expected_csv and sha(receipt_path) == expected_receipt
        actual_geff, file_count = tree_sha(geff_path)
        assert file_count == 21 and actual_geff == expected_geff
        input_pins.append({"dataset": name, "graph_csv_sha256": expected_csv,
                           "graph_receipt_sha256": expected_receipt,
                           "gt_geff_tree_sha256": expected_geff, "gt_files": file_count})

    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    rows, official_rows = [], []
    for name, prior_attr, prior_occupied, recorded_row in zip(
            SOURCE_IDS, PRIOR_ATTR["rows"], PRIOR_OCCUPIED["rows"], recorded["rows"]):
        assert prior_attr["dataset"] == prior_occupied["dataset"] == recorded_row["dataset"] == name
        graph = graphs.pop(name)
        ids = sorted(graph["nodes"])
        index = {node_id: offset for offset, node_id in enumerate(ids)}
        points = np.asarray([graph["nodes"][node_id] for node_id in ids], dtype=float).reshape((-1, 4))
        edges = [(index[source], index[target], 1.0, 0.0) for source, target in graph["edges"]]
        pred = build_graph(points, edges)
        ds = open_dataset(DATA / (name + ".zarr"), require_tracks=True, load_image=False)
        metric = evaluate(pred, ds.tracks, scale=ds.scale)
        recall = node_recall(pred, ds.tracks) if pred.num_nodes() and pred.num_edges() else 0.0
        estimate = (GeffMetadata.read(DATA / (name + ".geff")).extra or {})["estimated_number_of_nodes"]
        official = {"dataset": name, **per_sample_metrics(metric, float(estimate), recall)}
        for expected in (recorded_row, prior_attr["official"]):
            for key, value in expected.items():
                if key == "dataset":
                    assert official[key] == value
                    continue
                assert (official[key] == value if isinstance(value, int) else
                        math.isclose(official[key], value, rel_tol=0, abs_tol=1e-12)), (name, key)
        pred_to_gt, gt_to_pred = matched_maps(pred, td)
        decomposition = edge_decomposition(graph_edges(pred, td), graph_edges(ds.tracks, td),
                                           pred_to_gt, gt_to_pred)
        assert decomposition == prior_attr["decomposition"]
        row = _movie(name, pred, ds.tracks, pred_to_gt, gt_to_pred, ds.scale,
                     prior_attr, prior_occupied["association_details"])
        rows.append(row)
        official_rows.append(official)
        print(json.dumps({"done": name, "edges": row["gt_edges"],
                          "nonconsecutive": row["nonconsecutive_gt_edges"]}),
              file=sys.stderr, flush=True)
        del graph, ids, index, points, edges, pred, ds
        gc.collect()
    assert not graphs
    baseline = summarise(official_rows)
    for key, value in recorded["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), key
    assert math.isclose(baseline["score"], SOURCE_SCORE, rel_tol=0, abs_tol=1e-12)

    cases = [case for row in rows for case in row["cases"]]
    consecutive = [case for case in cases if case["frame_delta"] == 1]
    summaries = {edge_class: _distribution([case["distance_um"] for case in consecutive
                                            if case["class"] == edge_class])
                 for edge_class in ("tp", "endpoint_limited_fn", "association_limited_fn")}
    bins = _bins(consecutive)
    short, long = bins["at_most_7um"], bins["over_7um"]
    ratio = (summaries["association_limited_fn"]["median"] / summaries["tp"]["median"]
             if summaries["tp"]["median"] and summaries["association_limited_fn"]["median"]
             is not None else None)
    relative_recall = (long["recall"] / short["recall"]
                       if long["recall"] is not None and short["recall"] else None)
    direction_movies = [row["dataset"] for row in rows if row["direction_consistent"]]
    gate_pass = (ratio is not None and ratio >= 2.0 and relative_recall is not None
                 and relative_recall <= 0.5 and len(direction_movies) >= 6)
    assert len(cases) == 2039
    assert collections.Counter(case["class"] for case in cases) == {
        "tp": 1799, "endpoint_limited_fn": 153, "association_limited_fn": 87}
    assert sum(row["consecutive_gt_edges"] for row in rows) == len(consecutive)
    assert sum(row["nonconsecutive_gt_edges"] for row in rows) == len(cases) - len(consecutive)
    return {"status": "PASS_EXP227_SOURCE10_GT_EDGE_DISPLACEMENT_AUDIT",
            "source_score": SOURCE_SCORE, "source_graph_gate": gate_receipt["status"],
            "rows": rows,
            "pooled": {"gt_edges": len(cases), "consecutive_gt_edges": len(consecutive),
                       "nonconsecutive_gt_edges": len(cases) - len(consecutive),
                       "class_counts_all_edges": dict(collections.Counter(case["class"] for case in cases)),
                       "displacement_um": summaries, "recall_by_distance": bins,
                       "association_fn_to_tp_median_ratio": ratio,
                       "long_to_short_recall_ratio": relative_recall,
                       "direction_consistent_movies": direction_movies,
                       "required_direction_consistent_movies": 6,
                       "required_median_ratio": 2.0,
                       "maximum_long_to_short_recall_ratio": 0.5,
                       "long_motion_research_gate": "PASS" if gate_pass else "FAIL"},
            "inputs": input_pins,
            "scorer_pins": {"code_manifest_sha256": SCORER_MANIFEST_SHA,
                            "score_config_sha256": SCORE_CONFIG_SHA,
                            "graph_status_sha256": GRAPH_STATUS_SHA,
                            "score_result_sha256": SCORE_RESULT_SHA,
                            "score_gate_sha256": SCORE_GATE_SHA,
                            "evaluator_config_sha256": config["evaluator_config_sha256"]},
            "elapsed_seconds": time.time() - started,
            "target6bba_access": False, "candidate_tuning": False,
            "limitations": ["Post hoc source-inner training-monitor movies, not honest OOF.",
                            "Official matching is conditional on this fixed predicted graph.",
                            "GT edges and cells cluster within only eight movies.",
                            "Displacement association is diagnostic, not a model intervention or score gain."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
