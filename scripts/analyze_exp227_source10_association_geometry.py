"""Measure source8 association occupant geometry after the sealed scorer gate."""

import collections
import gc
import time


def _summary(values):
    import numpy as np

    if not values:
        return None
    array = np.asarray(values, dtype=float)
    assert np.all(np.isfinite(array))
    return {"min": float(array.min()), "q25": float(np.quantile(array, 0.25)),
            "median": float(np.median(array)), "q75": float(np.quantile(array, 0.75)),
            "max": float(array.max())}


def _movie(name, pred, gt, pred_to_gt, gt_to_pred, scale, prior):
    import numpy as np
    import tracksdata as td

    key = td.DEFAULT_ATTR_KEYS.NODE_ID
    nodes = {int(row[key]): row for row in pred.node_attrs().iter_rows(named=True)}
    gt_edges = set(graph_edges(gt, td))
    pred_edges = set(graph_edges(pred, td))
    pred_out = collections.defaultdict(set)
    for source, target in pred_edges:
        pred_out[source].add(target)
    xyz_scale = np.asarray(scale, dtype=float)
    assert xyz_scale.shape == (3,) and np.all(np.isfinite(xyz_scale)) and np.all(xyz_scale > 0)

    def point(node_id):
        row = nodes[node_id]
        return np.asarray([float(row[axis]) for axis in ("z", "y", "x")]) * xyz_scale

    def distance(left, right):
        value = float(np.linalg.norm(point(left) - point(right)))
        assert np.isfinite(value)
        return value

    association = []
    for source, target in sorted(gt_edges):
        ps, pt = gt_to_pred.get(source), gt_to_pred.get(target)
        if ps is None or pt is None or (ps, pt) in pred_edges:
            continue
        outgoing = sorted(pred_out.get(ps, set()))
        types = {"other_gt" if child in pred_to_gt else "unmatched" for child in outgoing}
        if not outgoing:
            kind = "absent"
        elif types == {"other_gt"}:
            kind = "other_gt_only"
        elif types == {"unmatched"}:
            kind = "unmatched_only"
        else:
            assert types == {"other_gt", "unmatched"}
            kind = "mixed"
        association.append({"gt_source_id": source, "gt_target_id": target,
                            "pred_source_id": ps, "pred_target_id": pt,
                            "source_outgoing_class": kind,
                            "source_outgoing_count": len(outgoing)})
    assert association == prior["association_details"], name
    assert len(association) == prior["association_limited_fn"]
    assert dict(collections.Counter(row["source_outgoing_class"] for row in association)) == (
        prior["association_source_outgoing_classes"])

    cases = []
    for row in association:
        if row["source_outgoing_class"] != "unmatched_only":
            continue
        ps, pt = row["pred_source_id"], row["pred_target_id"]
        occupants = sorted(pred_out[ps])
        assert len(occupants) == row["source_outgoing_count"] and occupants
        assert all(child not in pred_to_gt for child in occupants)
        source_t = int(nodes[ps]["t"])
        target_t = int(nodes[pt]["t"])
        assert target_t == source_t + 1
        assert all(int(nodes[child]["t"]) == target_t for child in occupants)
        child_rows = [
            {"pred_node_id": child,
             "occupant_to_matched_target_um": distance(child, pt),
             "source_to_occupant_um": distance(ps, child)}
            for child in occupants
        ]
        nearest = min(child_rows, key=lambda item: (item["occupant_to_matched_target_um"],
                                                    item["pred_node_id"]))
        cases.append({"dataset": name, "gt_source_id": row["gt_source_id"],
                      "gt_target_id": row["gt_target_id"], "pred_source_id": ps,
                      "pred_target_id": pt, "source_t": source_t,
                      "matched_target_t": target_t,
                      "source_to_matched_target_um": distance(ps, pt),
                      "occupants": child_rows, "nearest_occupant_pred_id": nearest["pred_node_id"],
                      "min_occupant_to_matched_target_um": nearest["occupant_to_matched_target_um"],
                      "within_5um": nearest["occupant_to_matched_target_um"] <= 5.0})
    expected = prior["association_source_outgoing_classes"].get("unmatched_only", 0)
    assert len(cases) == expected
    return {"dataset": name, "association_limited_fn": len(association),
            "unmatched_only_cases": len(cases),
            "within_5um": sum(case["within_5um"] for case in cases),
            "outgoing_unmatched_occupants": sum(len(case["occupants"]) for case in cases),
            "min_occupant_to_target_um": _summary(
                [case["min_occupant_to_matched_target_um"] for case in cases]),
            "source_to_matched_target_um": _summary(
                [case["source_to_matched_target_um"] for case in cases]),
            "source_to_occupant_um": _summary(
                [child["source_to_occupant_um"] for case in cases for child in case["occupants"]]),
            "cases": cases}


def main():
    import numpy as np
    import tracksdata as td
    from geff import GeffMetadata

    started = time.time()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert tuple(PINS) == SOURCE_IDS and all(name.startswith("44b6_") for name in SOURCE_IDS)
    assert PRIOR_OCCUPIED["status"] == "PASS_EXP227_SOURCE10_OCCUPIED_LINKS"
    assert PRIOR_OCCUPIED["source_score"] == SOURCE_SCORE
    assert PRIOR_OCCUPIED["source_graph_gate"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
    assert PRIOR_OCCUPIED["totals"]["association_limited_fn"] == 87
    assert PRIOR_OCCUPIED["totals"]["association_source_outgoing_classes"] == (
        {"unmatched_only": 69, "absent": 15, "other_gt_only": 3})
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
    official_config = json.loads(Path(config["evaluator_config"]).read_text())
    assert sha(Path(config["evaluator_config"])) == config["evaluator_config_sha256"]
    assert official_config["repo_path"] == config["repo"]
    evaluator_pins(official_config)
    # The graph and evaluator gate above precedes every source-label read.
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    recorded = json.loads((SCORER_RUN / "output/result.json").read_text())
    assert recorded["status"] == "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    assert math.isclose(recorded["summary"]["score"], SOURCE_SCORE, rel_tol=0, abs_tol=1e-12)
    previous = {row["dataset"]: row for row in recorded["rows"]}

    rows, official_rows, input_pins = [], [], []
    for name, prior in zip(SOURCE_IDS, PRIOR_OCCUPIED["rows"]):
        assert prior["dataset"] == name
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
        graph = graphs.pop(name)
        ids = sorted(graph["nodes"])
        index = {node_id: offset for offset, node_id in enumerate(ids)}
        points = np.asarray([graph["nodes"][node_id] for node_id in ids], dtype=float).reshape((-1, 4))
        edges = [(index[source], index[target], 1.0, 0.0) for source, target in graph["edges"]]
        pred = build_graph(points, edges)
        ds = open_dataset(DATA / (name + ".zarr"), require_tracks=True, load_image=False)
        metric = evaluate(pred, ds.tracks, scale=ds.scale)
        recall = node_recall(pred, ds.tracks) if pred.num_nodes() and pred.num_edges() else 0.0
        estimate = (GeffMetadata.read(geff_path).extra or {})["estimated_number_of_nodes"]
        official = {"dataset": name, **per_sample_metrics(metric, float(estimate), recall)}
        for key, value in previous[name].items():
            if key != "dataset":
                assert (official[key] == value if isinstance(value, int) else
                        math.isclose(official[key], value, rel_tol=0, abs_tol=1e-12)), (name, key)
        pred_to_gt, gt_to_pred = matched_maps(pred, td)
        decomposition = edge_decomposition(graph_edges(pred, td), graph_edges(ds.tracks, td),
                                           pred_to_gt, gt_to_pred)
        assert decomposition["fn_both_endpoints_matched_link_missing"] == prior["association_limited_fn"]
        row = _movie(name, pred, ds.tracks, pred_to_gt, gt_to_pred, ds.scale, prior)
        rows.append(row)
        official_rows.append(official)
        print(json.dumps({"done": name, "cases": row["unmatched_only_cases"],
                          "within_5um": row["within_5um"]}), file=sys.stderr, flush=True)
        del graph, ids, index, points, edges, pred, ds
        gc.collect()
    assert not graphs
    baseline = summarise(official_rows)
    for key, value in recorded["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), key
    total_cases = sum(row["unmatched_only_cases"] for row in rows)
    total_near = sum(row["within_5um"] for row in rows)
    assert total_cases == 69
    assert sum(row["association_limited_fn"] for row in rows) == 87
    assert len({(case["dataset"], case["gt_source_id"])
                for row in rows for case in row["cases"]}) == 69
    all_cases = [case for row in rows for case in row["cases"]]
    return {"status": "PASS_EXP227_SOURCE10_ASSOCIATION_GEOMETRY_AUDIT",
            "source_score": SOURCE_SCORE,
            "source_graph_gate": gate_receipt["status"],
            "rows": rows,
            "totals": {"association_limited_fn": 87, "unmatched_only_cases": total_cases,
                       "outgoing_unmatched_occupants": sum(row["outgoing_unmatched_occupants"] for row in rows),
                       "within_5um": total_near, "required_within_5um": 35,
                       "plausible_colocation_gate": "PASS" if total_near >= 35 else "FAIL",
                       "min_occupant_to_target_um": _summary(
                           [case["min_occupant_to_matched_target_um"] for case in all_cases]),
                       "source_to_matched_target_um": _summary(
                           [case["source_to_matched_target_um"] for case in all_cases]),
                       "source_to_occupant_um": _summary(
                           [child["source_to_occupant_um"] for case in all_cases
                            for child in case["occupants"]])},
            "inputs": input_pins,
            "scorer_pins": {"code_manifest_sha256": SCORER_MANIFEST_SHA,
                            "score_config_sha256": SCORE_CONFIG_SHA,
                            "graph_status_sha256": GRAPH_STATUS_SHA,
                            "score_result_sha256": SCORE_RESULT_SHA,
                            "score_gate_sha256": SCORE_GATE_SHA,
                            "evaluator_config_sha256": config["evaluator_config_sha256"]},
            "elapsed_seconds": time.time() - started,
            "target6bba_access": False, "candidate_tuning": False,
            "limitations": ["Post hoc source-inner epoch10 training monitor; not target OOF.",
                            "Official node matching is conditional on this fixed final graph.",
                            "An unmatched predicted occupant may represent a real cell.",
                            "Distance alone cannot justify reassociation or predict score change.",
                            "Cases cluster by movie; this is not 69 independent embryo replicates."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
