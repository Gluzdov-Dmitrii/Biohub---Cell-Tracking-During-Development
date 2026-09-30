"""Source8 endpoint-FN node features; appended to the pinned attribution prelude.

This file is intentionally run only by run_exp227_source10_fn_features_remote.py,
which prepends the unchanged fixed-node attribution source. It never selects a
candidate or reads target6bba data.
"""

import collections
import gc
import statistics
import time


def _patch_feature(volume, z, y, x):
    import numpy as np

    z, y, x = (int(round(value)) for value in (z, y, x))
    z = max(0, min(volume.shape[0] - 1, z))
    y = max(0, min(volume.shape[1] - 1, y))
    x = max(0, min(volume.shape[2] - 1, x))
    outer = volume[max(0, z-2):z+3, max(0, y-6):y+7, max(0, x-6):x+7]
    inner = volume[max(0, z-1):z+2, max(0, y-2):y+3, max(0, x-2):x+3]
    # A cropped background is acceptable at the border; geometry records it.
    center = float(np.mean(inner, dtype=np.float64))
    bg = float(np.median(outer))
    spread = float(np.std(outer, dtype=np.float64))
    return center, center - bg, (center - bg) / max(spread, 1e-6)


def _movie_features(name, ds, matched, gt_edges, image_path):
    import numpy as np
    import tracksdata as td
    import zarr

    node_rows = list(ds.tracks.node_attrs().iter_rows(named=True))
    nodes = {int(row[td.DEFAULT_ATTR_KEYS.NODE_ID]): row for row in node_rows}
    edge_nodes = {node for edge in gt_edges for node in edge}
    assert edge_nodes <= set(nodes)
    unmatched = edge_nodes - set(matched)
    affected = {node for source, target in gt_edges
                for node in (source, target) if node not in matched}
    assert affected == unmatched
    out = collections.defaultdict(set)
    for source, target in gt_edges:
        out[source].add(target)
    division_sources = [node for node, targets in out.items() if len(targets) > 1]
    division_times = [int(nodes[node]["t"]) for node in division_sources]

    by_time = collections.defaultdict(list)
    for node in edge_nodes:
        by_time[int(nodes[node]["t"])].append(node)
    root = zarr.open(str(image_path), mode="r")
    image = root if hasattr(root, "shape") else root["0"]
    assert tuple(image.shape) == tuple(ds.image_shape)
    assert len(image.shape) == 4
    scale = np.asarray(ds.scale, dtype=float)
    assert scale.shape == (3,) and np.all(scale > 0)
    bounds = np.asarray(ds.image_shape[1:], dtype=float) - 1
    result = []
    for t, frame_nodes in sorted(by_time.items()):
        # One frame at a time bounds the decoded image to 64x256x256 voxels.
        volume = np.asarray(image[t])
        xyz = np.asarray([[float(nodes[node][axis]) for axis in ("z", "y", "x")]
                          for node in frame_nodes], dtype=float)
        assert np.all(np.isfinite(xyz)) and np.all(xyz >= 0) and np.all(xyz <= bounds)
        physical = xyz * scale
        distances = np.sqrt(np.sum((physical[:, None, :] - physical[None, :, :]) ** 2, axis=-1))
        np.fill_diagonal(distances, np.inf)
        nearest = np.min(distances, axis=1)
        nearest = np.where(np.isfinite(nearest), nearest,
                           float(np.linalg.norm(bounds * scale)))
        neighbors6 = np.sum(distances < 6.0, axis=1)
        for index, node in enumerate(frame_nodes):
            center, contrast, contrast_snr = _patch_feature(volume, *xyz[index])
            border = float(np.min(np.minimum(xyz[index], bounds - xyz[index]) * scale))
            result.append({"node": node, "missed": node in unmatched,
                           "center_intensity": center, "local_contrast": contrast,
                           "contrast_snr": contrast_snr,
                           "nearest_um": float(nearest[index]),
                           "neighbors6": int(neighbors6[index]),
                           "border_um": border, "time_fraction": t / max(1, image.shape[0]-1),
                           "division_time_distance": min((abs(t-d) for d in division_times), default=None),
                           "division_parent": node in division_sources})
        del volume
    assert len(result) == len(edge_nodes)
    assert sum(row["missed"] for row in result) == len(unmatched)
    del image, root, node_rows, nodes
    gc.collect()
    return result, len(division_sources)


def _quartile_low(rows, feature):
    import numpy as np
    values = np.asarray([row[feature] for row in rows], dtype=float)
    threshold = float(np.quantile(values, 0.25))
    return threshold, lambda row: row[feature] <= threshold


def _stratum(rows, check):
    exposed = [row for row in rows if check(row)]
    other = [row for row in rows if not check(row)]
    if not exposed or not other:
        return None
    a = sum(row["missed"] for row in exposed)
    b = sum(row["missed"] for row in other)
    return {"exposed_nodes": len(exposed), "exposed_missed": a,
            "other_nodes": len(other), "other_missed": b,
            "exposed_rate": a / len(exposed), "other_rate": b / len(other),
            "risk_difference": a / len(exposed) - b / len(other)}


def _summarize(rows):
    import numpy as np
    missed = [row for row in rows if row["missed"]]
    matched = [row for row in rows if not row["missed"]]
    assert missed and matched
    output = {"eligible_nodes": len(rows), "endpoint_missed_nodes": len(missed),
              "miss_rate": len(missed) / len(rows)}
    for feature in ("center_intensity", "local_contrast", "contrast_snr",
                    "nearest_um", "neighbors6", "border_um", "time_fraction"):
        output[feature] = {
            "missed_median": float(np.median([row[feature] for row in missed])),
            "matched_median": float(np.median([row[feature] for row in matched]))}
    for name, feature in (("low_intensity_q1", "center_intensity"),
                          ("low_contrast_q1", "local_contrast"),
                          ("low_contrast_snr_q1", "contrast_snr")):
        threshold, check = _quartile_low(rows, feature)
        output[name] = {"threshold": threshold, **_stratum(rows, check)}
        if name == "low_contrast_snr_q1":
            output["low_contrast_snr_q1_interior"] = _stratum(
                [row for row in rows if row["border_um"] >= 5], check)
            output["low_contrast_snr_q1_border"] = _stratum(
                [row for row in rows if row["border_um"] < 5], check)
    output["crowded_nearest_lt6um"] = _stratum(rows, lambda row: row["nearest_um"] < 6)
    output["crowded_nearest_lt12um"] = _stratum(rows, lambda row: row["nearest_um"] < 12)
    output["crowded_neighbors6_ge2"] = _stratum(rows, lambda row: row["neighbors6"] >= 2)
    output["border_lt5um"] = _stratum(rows, lambda row: row["border_um"] < 5)
    output["late_time_q4"] = _stratum(rows, lambda row: row["time_fraction"] >= .75)
    output["near_division_2frames"] = (None if all(row["division_time_distance"] is None for row in rows)
                                       else _stratum(rows, lambda row:
                                                     row["division_time_distance"] is not None and
                                                     row["division_time_distance"] <= 2))
    return output


def _across_movies(rows):
    keys = ("low_intensity_q1", "low_contrast_q1", "low_contrast_snr_q1",
            "low_contrast_snr_q1_interior", "low_contrast_snr_q1_border",
            "crowded_nearest_lt6um", "crowded_nearest_lt12um", "crowded_neighbors6_ge2", "border_lt5um",
            "late_time_q4", "near_division_2frames")
    result = {}
    for key in keys:
        samples = [row["features"][key] for row in rows if row["features"][key] is not None]
        if not samples:
            result[key] = {"movies": 0}
            continue
        result[key] = {"movies": len(samples),
                       "higher_miss_rate_movies": sum(sample["risk_difference"] > 0 for sample in samples),
                       "lower_miss_rate_movies": sum(sample["risk_difference"] < 0 for sample in samples),
                       "macro_risk_difference": statistics.mean(sample["risk_difference"] for sample in samples),
                       "median_risk_difference": statistics.median(sample["risk_difference"] for sample in samples),
                       "pooled_exposed": sum(sample["exposed_nodes"] for sample in samples),
                       "pooled_exposed_missed": sum(sample["exposed_missed"] for sample in samples),
                       "pooled_other": sum(sample["other_nodes"] for sample in samples),
                       "pooled_other_missed": sum(sample["other_missed"] for sample in samples)}
    return result


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
    assert Path(config["inference_run"]) == INFERENCE_RUN
    assert Path(config["data_dir"]) == DATA
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
    # Source labels and images are first opened after the exact graph/evaluator gate.
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    recorded = json.loads((SCORER_RUN / "output/result.json").read_text())
    assert recorded["status"] == "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    assert math.isclose(recorded["summary"]["score"], SOURCE_SCORE, abs_tol=1e-12)
    recorded_rows = {row["dataset"]: row for row in recorded["rows"]}
    output_rows = []
    official_rows = []
    inputs = []
    for name in SOURCE_IDS:
        csv_path = INFERENCE_RUN / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        geff_path = DATA / (name + ".geff")
        expected_csv, expected_receipt, expected_geff = PINS[name]
        assert sha(csv_path) == expected_csv and sha(receipt_path) == expected_receipt
        actual_geff, file_count = tree_sha(geff_path)
        assert file_count == 21 and actual_geff == expected_geff
        inputs.append({"dataset": name, "graph_csv_sha256": expected_csv,
                       "graph_receipt_sha256": expected_receipt,
                       "gt_geff_tree_sha256": expected_geff})
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
        row = {"dataset": name, **per_sample_metrics(metric, float(estimate), recall)}
        for key, value in recorded_rows[name].items():
            if key != "dataset":
                assert (row[key] == value if isinstance(value, int) else
                        math.isclose(row[key], value, rel_tol=0, abs_tol=1e-12)), (name, key)
        _, gt_to_pred = matched_maps(pred, td)
        gt_edges = graph_edges(ds.tracks, td)
        decomposition = edge_decomposition(graph_edges(pred, td), gt_edges,
                                           {pred_id: gt_id for gt_id, pred_id in gt_to_pred.items()},
                                           gt_to_pred)
        assert decomposition["edge_tp"] == row["edge_tp"]
        assert sum(decomposition[key] for key in (
            "fn_missing_both_endpoints", "fn_missing_source_endpoint",
            "fn_missing_target_endpoint")) + decomposition["fn_both_endpoints_matched_link_missing"] == row["edge_fn"]
        features, divisions = _movie_features(name, ds, gt_to_pred, gt_edges, DATA / (name + ".zarr"))
        summary = _summarize(features)
        output_rows.append({"dataset": name, "official_edge_fn": row["edge_fn"],
                            "endpoint_limited_fn": sum(decomposition[key] for key in (
                                "fn_missing_both_endpoints", "fn_missing_source_endpoint",
                                "fn_missing_target_endpoint")),
                            "division_parents": divisions, "features": summary})
        official_rows.append(row)
        print(json.dumps({"done": name, "missed": summary["endpoint_missed_nodes"],
                          "eligible": summary["eligible_nodes"]}), file=sys.stderr, flush=True)
        del graph, ids, index, points, edges, pred, ds, features
        gc.collect()
    baseline = summarise(official_rows)
    for key, value in recorded["summary"].items():
        assert (baseline[key] == value if isinstance(value, int) else
                math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-12)), key
    assert sum(row["endpoint_limited_fn"] for row in output_rows) == 153
    return {"status": "PASS_EXP227_SOURCE10_FN_FEATURES", "evidence_class":
            "post hoc source-inner training monitor, not target OOF or a tuned candidate",
            "source_score": SOURCE_SCORE, "source_graph_gate": gate_receipt["status"],
            "inputs": inputs, "movies": output_rows, "across_movies": _across_movies(output_rows),
            "endpoint_limited_fn": 153,
            "distinct_endpoint_missed_nodes": sum(row["features"]["endpoint_missed_nodes"] for row in output_rows),
            "elapsed_seconds": time.time() - started, "target6bba_access": False,
            "candidate_tuning": False,
            "limitations": ["Same eight source44 inner movies monitored training; no target OOF.",
                            "Official node matches are conditional on the epoch10 prediction graph.",
                            "Node and edge outcomes correlate within movies; eight movies are the unit of replication.",
                            "Raw local intensity and contrast are descriptive, not calibrated detection logits.",
                            "GT division events are sparse; division proximity is descriptive only."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
