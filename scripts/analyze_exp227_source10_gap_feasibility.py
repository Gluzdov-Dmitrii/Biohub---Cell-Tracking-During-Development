"""GT-aware source8 feasibility audit; appended to pinned attribution prelude."""

import collections
import gc
import time


def _minimax_radius(points):
    """Smallest enclosing-ball radius for three 3D points (physical µm)."""
    import numpy as np

    p = np.asarray(points, dtype=float)
    candidates = [*p, *((p[i] + p[j]) / 2 for i in range(3) for j in range(i + 1, 3))]
    a, b = p[1] - p[0], p[2] - p[0]
    gram = np.array([[a @ a, a @ b], [a @ b, b @ b]], dtype=float)
    if np.linalg.det(gram) > 1e-12:
        alpha, beta = np.linalg.solve(gram, [a @ a / 2, b @ b / 2])
        candidates.append(p[0] + alpha * a + beta * b)
    return min(float(np.max(np.linalg.norm(p - center, axis=1))) for center in candidates)


def _matching_size(pairs):
    """Maximum one-to-one matching of supported track-end/start pairs."""
    by_left = collections.defaultdict(list)
    for left, right in pairs:
        by_left[left].append(right)
    owner = {}

    def augment(left, seen):
        for right in sorted(set(by_left[left])):
            if right in seen:
                continue
            seen.add(right)
            if right not in owner or augment(owner[right], seen):
                owner[right] = left
                return True
        return False

    return sum(augment(left, set()) for left in sorted(by_left))


def _movie(name, graph, pred, ds, matched):
    import numpy as np
    import tracksdata as td
    from scipy.spatial import cKDTree

    node_key = td.DEFAULT_ATTR_KEYS.NODE_ID
    gt_nodes = {int(row[node_key]): row for row in ds.tracks.node_attrs().iter_rows(named=True)}
    pred_nodes = {int(row[node_key]): row for row in pred.node_attrs().iter_rows(named=True)}
    gt_edges = set(graph_edges(ds.tracks, td))
    pred_edges = set(graph_edges(pred, td))
    gt_in, gt_out = collections.defaultdict(set), collections.defaultdict(set)
    pred_in, pred_out = collections.defaultdict(set), collections.defaultdict(set)
    for source, target in gt_edges:
        gt_out[source].add(target)
        gt_in[target].add(source)
    for source, target in pred_edges:
        pred_out[source].add(target)
        pred_in[target].add(source)
    edge_nodes = set(gt_in) | set(gt_out)
    missed = edge_nodes - set(matched)
    scale = np.asarray(ds.scale, dtype=float)
    assert len(scale) == 3 and np.all(scale > 0)
    pred_by_t = collections.defaultdict(list)
    for node, row in pred_nodes.items():
        pred_by_t[int(row["t"])].append([float(row[axis]) for axis in ("z", "y", "x")])
    frame_trees = {t: cKDTree(np.asarray(coords, dtype=float) * scale)
                   for t, coords in pred_by_t.items() if coords}

    stages = collections.Counter()
    candidates = []
    for node in sorted(missed):
        stages["unmatched_edge_nodes"] += 1
        before, after = gt_in.get(node, set()), gt_out.get(node, set())
        if len(before) != 1 or len(after) != 1:
            continue
        source, target = next(iter(before)), next(iter(after))
        t = int(gt_nodes[node]["t"])
        if int(gt_nodes[source]["t"]) != t - 1 or int(gt_nodes[target]["t"]) != t + 1:
            continue
        stages["linear_gt_one_frame_gap"] += 1
        ps, pt = matched.get(source), matched.get(target)
        if ps is None or pt is None:
            continue
        if int(pred_nodes[ps]["t"]) != t - 1 or int(pred_nodes[pt]["t"]) != t + 1:
            continue
        stages["both_gt_anchors_matched"] += 1
        if ps not in pred_in or pt not in pred_out:
            continue
        stages["anchors_supported"] += 1
        if ps in pred_out or pt in pred_in:
            continue
        stages["pred_gap_still_open"] += 1
        physical = [np.asarray([float(row[axis]) for axis in ("z", "y", "x")]) * scale
                    for row in (pred_nodes[ps], gt_nodes[node], pred_nodes[pt])]
        d_source = float(np.linalg.norm(physical[0] - physical[1]))
        d_target = float(np.linalg.norm(physical[1] - physical[2]))
        radius = _minimax_radius(physical)
        if radius <= 7.0 + 1e-9:
            stages["any_point_within_7um_of_both_anchors_and_gt"] += 1
        center_pass = d_source <= 7.0 + 1e-9 and d_target <= 7.0 + 1e-9
        if center_pass:
            stages["gt_center_within_7um_of_both_anchors"] += 1
        nearest = (float(frame_trees[t].query(physical[1], k=1)[0])
                   if t in frame_trees else float("inf"))
        reuse_pass = nearest > 3.2 + 1e-9
        if reuse_pass:
            stages["gt_center_clear_of_retained_node_3p2um"] += 1
        if center_pass and reuse_pass:
            stages["gt_center_passes_both_gates"] += 1
        candidates.append({"gt": node, "pred_source": ps, "pred_target": pt,
                           "radius": radius, "center_geometry": center_pass,
                           "center_reuse": reuse_pass})

    topology = [(row["pred_source"], row["pred_target"]) for row in candidates]
    liberal = [(row["pred_source"], row["pred_target"]) for row in candidates if row["radius"] <= 7.0 + 1e-9]
    center = [(row["pred_source"], row["pred_target"]) for row in candidates
              if row["center_geometry"] and row["center_reuse"]]
    assert stages["pred_gap_still_open"] == len(candidates)
    # Each unique linear GT node has exactly two current FN edges, but one-to-one
    # endpoint matching can admit fewer nodes than the raw candidate count.
    for row in candidates:
        node = row["gt"]
        assert all((source, node) in gt_edges for source in gt_in[node])
        assert all((node, target) in gt_edges for target in gt_out[node])
    return {"dataset": name, "stages": dict(stages),
            "topology_only_max_nodes_one_to_one": _matching_size(topology),
            "topology_only_edge_fn_upper_bound": 2 * _matching_size(topology),
            "geometry_any_point_max_nodes_one_to_one": _matching_size(liberal),
            "geometry_any_point_edge_fn_upper_bound": 2 * _matching_size(liberal),
            "gt_center_proxy_max_nodes_one_to_one": _matching_size(center),
            "gt_center_proxy_edge_fn_conditional_ceiling": 2 * _matching_size(center)}


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
    # Exact graph/evaluator gate above precedes every source-label GEFF access.
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
        _, gt_to_pred = matched_maps(pred, td)
        result = _movie(name, graph, pred, ds, gt_to_pred)
        assert result["stages"].get("unmatched_edge_nodes", 0) == ds.tracks.num_nodes() - len(gt_to_pred)
        rows.append(result)
        official_rows.append(official)
        print(json.dumps({"done": name, "stages": result["stages"]}), file=sys.stderr, flush=True)
        del graph, ids, index, points, edges, pred, ds
        gc.collect()
    baseline = summarise(official_rows)
    for key, value in recorded["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), key
    totals = {key: sum(row[key] for row in rows) for key in (
        "topology_only_max_nodes_one_to_one", "topology_only_edge_fn_upper_bound",
        "geometry_any_point_max_nodes_one_to_one", "geometry_any_point_edge_fn_upper_bound",
        "gt_center_proxy_max_nodes_one_to_one", "gt_center_proxy_edge_fn_conditional_ceiling")}
    totals["stages"] = {key: sum(row["stages"].get(key, 0) for row in rows)
                        for key in sorted({key for row in rows for key in row["stages"]})}
    assert totals["stages"]["unmatched_edge_nodes"] == 115
    return {"status": "PASS_EXP227_SOURCE10_GAP_FEASIBILITY", "source_score": SOURCE_SCORE,
            "source_graph_gate": gate_receipt["status"], "rows": rows, "totals": totals,
            "inputs": input_pins, "elapsed_seconds": time.time() - started,
            "target6bba_access": False, "candidate_tuning": False,
            "definitions": {
                "topology_upper_bound": "2 FN edges per one-to-one matched supported open GT linear gap; ignores all spatial, reuse and logit gates",
                "geometry_any_point_upper_bound": "maximum two-sided 7um and official 7um GT-match ball intersection; ignores retained-node reuse and weak-peak/logit availability",
                "gt_center_proxy": "places ideal weak peak at GT coordinate, requires <=7um to both anchors and >3.2um from all retained nodes at that frame; conditional ceiling, not a general geometric upper bound"},
            "limitations": ["Post hoc epoch10 source-inner training monitor, not target OOF.",
                            "Weak logit peaks and probabilities were not stored; no candidate availability is measured.",
                            "Final retained graph and official matching do not identify whether a node was missed by detection, assignment or filtering.",
                            "One-to-one matching bounds are per movie; other graph changes could alter official matching and edge counts.",
                            "Even geometrically feasible gaps can be false associations or be removed by later filtering."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
