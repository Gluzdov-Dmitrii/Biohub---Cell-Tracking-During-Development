"""Source8 occupied-link attribution; appended to pinned attribution prelude."""

import collections
import gc
import time


def _movie(name, pred, gt, pred_to_gt, gt_to_pred, scale):
    import numpy as np
    import tracksdata as td

    key = td.DEFAULT_ATTR_KEYS.NODE_ID
    gt_nodes = {int(row[key]): row for row in gt.node_attrs().iter_rows(named=True)}
    pred_nodes = {int(row[key]): row for row in pred.node_attrs().iter_rows(named=True)}
    gt_edges = set(graph_edges(gt, td))
    pred_edges = set(graph_edges(pred, td))
    gt_in, gt_out = collections.defaultdict(set), collections.defaultdict(set)
    pred_in, pred_out = collections.defaultdict(set), collections.defaultdict(set)
    for source, target in gt_edges:
        gt_out[source].add(target)
        gt_in[target].add(source)
    for source, target in pred_edges:
        pred_out[source].add(target)
        pred_in[target].add(source)
    xyz_scale = np.asarray(scale, dtype=float)
    assert xyz_scale.shape == (3,) and np.all(xyz_scale > 0)

    def occupancy(node, missed_xyz):
        row = pred_nodes[node]
        xyz = np.asarray([float(row[axis]) for axis in ("z", "y", "x")], dtype=float)
        matched_gt = pred_to_gt.get(node)
        return {"pred_node_id": node,
                "match_class": "other_gt" if matched_gt is not None else "unmatched",
                "matched_gt_node_id": matched_gt,
                "distance_to_missed_gt_um": float(np.linalg.norm((xyz - missed_xyz) * xyz_scale)),
                "synthetic": "unknown_from_serialized_csv"}

    missing = (set(gt_in) | set(gt_out)) - set(gt_to_pred)
    stages = collections.Counter()
    occupied = []
    for node in sorted(missing):
        stages["unmatched_edge_nodes"] += 1
        before, after = gt_in.get(node, set()), gt_out.get(node, set())
        if len(before) != 1 or len(after) != 1:
            continue
        source, target = next(iter(before)), next(iter(after))
        t = int(gt_nodes[node]["t"])
        if int(gt_nodes[source]["t"]) != t - 1 or int(gt_nodes[target]["t"]) != t + 1:
            continue
        stages["linear_gt_one_frame_gap"] += 1
        ps, pt = gt_to_pred.get(source), gt_to_pred.get(target)
        if ps is None or pt is None:
            continue
        assert int(pred_nodes[ps]["t"]) == t - 1 and int(pred_nodes[pt]["t"]) == t + 1
        stages["both_gt_anchors_matched"] += 1
        if ps not in pred_in or pt not in pred_out:
            continue
        stages["anchors_supported"] += 1
        if ps not in pred_out and pt not in pred_in:
            stages["pred_gap_still_open"] += 1
            continue
        stages["occupied_anchor_gaps"] += 1
        missing_xyz = np.asarray([float(gt_nodes[node][axis]) for axis in ("z", "y", "x")])
        source_occupants = [occupancy(other, missing_xyz) for other in sorted(pred_out[ps])]
        target_occupants = [occupancy(other, missing_xyz) for other in sorted(pred_in[pt])]
        assert all(int(pred_nodes[row["pred_node_id"]]["t"]) == t
                   for row in source_occupants + target_occupants)
        shared = sorted(set(pred_out[ps]) & set(pred_in[pt]))
        assert len(shared) <= 1
        if shared:
            pattern = "same_intermediate"
        elif source_occupants and target_occupants:
            pattern = "different_intermediates"
        elif source_occupants:
            pattern = "source_outgoing_only"
        else:
            pattern = "target_incoming_only"
        occupied.append({"dataset": name, "gt_node_id": node, "t": t,
                         "gt_predecessor": source, "gt_successor": target,
                         "pred_source_anchor": ps, "pred_target_anchor": pt,
                         "source_outgoing": source_occupants,
                         "target_incoming": target_occupants,
                         "shared_intermediate_pred_node_id": shared[0] if shared else None,
                         "occupancy_pattern": pattern})
    assert len(occupied) == stages["occupied_anchor_gaps"]

    assoc = []
    for source, target in sorted(gt_edges):
        ps, pt = gt_to_pred.get(source), gt_to_pred.get(target)
        if ps is None or pt is None or (ps, pt) in pred_edges:
            continue
        outgoing = sorted(pred_out.get(ps, set()))
        types = {"other_gt" if node in pred_to_gt else "unmatched" for node in outgoing}
        if not outgoing:
            kind = "absent"
        elif types == {"other_gt"}:
            kind = "other_gt_only"
        elif types == {"unmatched"}:
            kind = "unmatched_only"
        else:
            assert types == {"other_gt", "unmatched"}
            kind = "mixed"
        assoc.append({"gt_source_id": source, "gt_target_id": target,
                      "pred_source_id": ps, "pred_target_id": pt,
                      "source_outgoing_class": kind,
                      "source_outgoing_count": len(outgoing)})
    occupied_patterns = collections.Counter(row["occupancy_pattern"] for row in occupied)
    outgoing_classes = collections.Counter(row["source_outgoing_class"] for row in assoc)
    source_occupants = [item for row in occupied for item in row["source_outgoing"]]
    target_occupants = [item for row in occupied for item in row["target_incoming"]]

    def occupant_summary(items):
        return {"edges": len(items),
                "matched_other_gt": sum(item["match_class"] == "other_gt" for item in items),
                "unmatched": sum(item["match_class"] == "unmatched" for item in items),
                "within_7um": sum(item["distance_to_missed_gt_um"] <= 7.0 for item in items),
                "over_7um": sum(item["distance_to_missed_gt_um"] > 7.0 for item in items),
                "median_distance_um": (float(np.median([item["distance_to_missed_gt_um"]
                                                         for item in items])) if items else None)}

    return {"dataset": name, "stages": dict(stages),
            "occupied_patterns": dict(occupied_patterns),
            "source_outgoing_occupants": occupant_summary(source_occupants),
            "target_incoming_occupants": occupant_summary(target_occupants),
            "occupied_details": occupied,
            "association_limited_fn": len(assoc),
            "association_source_outgoing_classes": dict(outgoing_classes),
            "association_distinct_gt_sources": len({row["gt_source_id"] for row in assoc}),
            "association_details": assoc}


def main():
    import numpy as np
    import tracksdata as td
    from geff import GeffMetadata

    started = time.time()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert tuple(PINS) == SOURCE_IDS and all(name.startswith("44b6_") for name in SOURCE_IDS)
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
    # Exact graph and evaluator gate above precedes every source-label read.
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    recorded = json.loads((SCORER_RUN / "output/result.json").read_text())
    assert recorded["status"] == "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    assert math.isclose(recorded["summary"]["score"], SOURCE_SCORE, abs_tol=1e-12)
    previous = {row["dataset"]: row for row in recorded["rows"]}
    rows, official_rows, input_pins = [], [], []
    for name in SOURCE_IDS:
        csv_path = INFERENCE_RUN / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        geff_path = DATA / (name + ".geff")
        expected_csv, expected_receipt, expected_geff = PINS[name]
        assert sha(csv_path) == expected_csv and sha(receipt_path) == expected_receipt
        actual_geff, file_count = tree_sha(geff_path)
        assert file_count == 21 and actual_geff == expected_geff
        input_pins.append({"dataset": name, "csv_sha256": expected_csv,
                           "receipt_sha256": expected_receipt, "geff_tree_sha256": expected_geff})
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
        assert decomposition["fn_both_endpoints_matched_link_missing"] == (
            previous[name]["edge_fn"] - sum(decomposition[key] for key in (
                "fn_missing_both_endpoints", "fn_missing_source_endpoint",
                "fn_missing_target_endpoint")))
        result = _movie(name, pred, ds.tracks, pred_to_gt, gt_to_pred, ds.scale)
        assert result["association_limited_fn"] == decomposition["fn_both_endpoints_matched_link_missing"]
        rows.append(result)
        official_rows.append(official)
        print(json.dumps({"done": name, "occupied": len(result["occupied_details"]),
                          "association_fn": result["association_limited_fn"]}),
              file=sys.stderr, flush=True)
        del graph, ids, index, points, edges, pred, ds
        gc.collect()
    baseline = summarise(official_rows)
    for key, value in recorded["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), key
    totals = {"occupied_anchor_gaps": sum(row["stages"].get("occupied_anchor_gaps", 0)
                                           for row in rows),
              "association_limited_fn": sum(row["association_limited_fn"] for row in rows),
              "association_distinct_gt_sources": sum(row["association_distinct_gt_sources"]
                                                     for row in rows)}
    totals["occupied_patterns"] = dict(sum((collections.Counter(row["occupied_patterns"])
                                             for row in rows), collections.Counter()))
    totals["association_source_outgoing_classes"] = dict(sum(
        (collections.Counter(row["association_source_outgoing_classes"]) for row in rows),
        collections.Counter()))
    totals["source_outgoing_occupants"] = {
        key: sum(row["source_outgoing_occupants"][key] for row in rows)
        for key in ("edges", "matched_other_gt", "unmatched", "within_7um", "over_7um")}
    totals["target_incoming_occupants"] = {
        key: sum(row["target_incoming_occupants"][key] for row in rows)
        for key in ("edges", "matched_other_gt", "unmatched", "within_7um", "over_7um")}
    assert totals["occupied_anchor_gaps"] == 20
    assert totals["association_limited_fn"] == 87
    assert sum(totals["association_source_outgoing_classes"].values()) == 87
    return {"status": "PASS_EXP227_SOURCE10_OCCUPIED_LINKS", "source_score": SOURCE_SCORE,
            "source_graph_gate": gate_receipt["status"], "rows": rows, "totals": totals,
            "inputs": input_pins, "elapsed_seconds": time.time() - started,
            "target6bba_access": False, "candidate_tuning": False,
            "synthetic_node_status": "Unavailable per node: final CSV omits Node.synthetic and graph receipt reports only aggregate synthetic counts.",
            "limitations": ["Post hoc source-inner epoch10 training monitor, not target OOF.",
                            "Official matching is conditional on the fixed predicted graph and can change after edits.",
                            "An occupied anchor may reflect correct links to another annotated cell; rewiring feasibility and score are not measured.",
                            "Repeated GT edges and shared source anchors are correlated; movie is the replication unit.",
                            "Final CSV does not preserve raw neural logits, ILP candidate probabilities or per-node synthetic flag."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
