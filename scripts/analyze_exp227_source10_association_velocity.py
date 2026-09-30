"""Fixed half-velocity diagnostic on sealed EXP227 epoch10 source8 graphs."""

import collections
import gc
import time


def _motion_movie(name, graph, scale, prior):
    import numpy as np

    xyz_scale = np.asarray(scale, dtype=float)
    assert xyz_scale.shape == (3,) and np.all(np.isfinite(xyz_scale)) and np.all(xyz_scale > 0)
    nodes = graph["nodes"]
    incoming = collections.defaultdict(set)
    for source, target in graph["edges"]:
        incoming[target].add(source)

    def physical(node_id):
        point = nodes[node_id]
        assert len(point) == 4
        result = np.asarray(point[1:], dtype=float) * xyz_scale
        assert np.all(np.isfinite(result))
        return result

    def norm(left, right):
        value = float(np.linalg.norm(left - right))
        assert np.isfinite(value)
        return value

    cases = []
    for raw in prior["cases"]:
        assert raw["dataset"] == name and len(raw["occupants"]) == 1
        ps, pt = raw["pred_source_id"], raw["pred_target_id"]
        child = raw["occupants"][0]["pred_node_id"]
        source_p, target_p, child_p = physical(ps), physical(pt), physical(child)
        source_t = int(nodes[ps][0])
        assert source_t == raw["source_t"]
        assert int(nodes[pt][0]) == int(nodes[child][0]) == source_t + 1
        raw_target = norm(source_p, target_p)
        raw_occupant = norm(source_p, child_p)
        raw_child_target = norm(child_p, target_p)
        assert abs(raw_target - raw["source_to_matched_target_um"]) <= 1e-9
        assert abs(raw_occupant - raw["occupants"][0]["source_to_occupant_um"]) <= 1e-9
        assert abs(raw_child_target - raw["occupants"][0]["occupant_to_matched_target_um"]) <= 1e-9
        parents = sorted(incoming.get(ps, set()))
        result = {"dataset": name, "gt_source_id": raw["gt_source_id"],
                  "gt_target_id": raw["gt_target_id"], "pred_source_id": ps,
                  "pred_target_id": pt, "occupant_pred_id": child,
                  "source_t": source_t,
                  "raw_source_to_matched_target_um": raw_target,
                  "raw_source_to_occupant_um": raw_occupant,
                  "raw_occupant_to_matched_target_um": raw_child_target,
                  "incoming_pred_node_ids": parents}
        if len(parents) != 1:
            result["valid_predecessor"] = False
            result["invalid_reason"] = "no_predecessor" if not parents else "multiple_predecessors"
            result["predecessor_pred_id"] = None
            result["motion_to_matched_target_um"] = None
            result["motion_to_occupant_um"] = None
            result["target_advantage_um"] = None
            result["target_advantage_at_least_2um"] = False
        else:
            predecessor = parents[0]
            result["predecessor_pred_id"] = predecessor
            if int(nodes[predecessor][0]) != source_t - 1:
                result["valid_predecessor"] = False
                result["invalid_reason"] = "nonconsecutive_predecessor"
                result["motion_to_matched_target_um"] = None
                result["motion_to_occupant_um"] = None
                result["target_advantage_um"] = None
                result["target_advantage_at_least_2um"] = False
            else:
                forecast = source_p + 0.5 * (source_p - physical(predecessor))
                motion_target = norm(forecast, target_p)
                motion_child = norm(forecast, child_p)
                margin = motion_child - motion_target
                result["valid_predecessor"] = True
                result["invalid_reason"] = None
                result["motion_to_matched_target_um"] = motion_target
                result["motion_to_occupant_um"] = motion_child
                result["target_advantage_um"] = margin
                result["target_advantage_at_least_2um"] = margin >= 2.0
        cases.append(result)
    valid = [row for row in cases if row["valid_predecessor"]]
    advantage = [row for row in valid if row["target_advantage_at_least_2um"]]
    return {"dataset": name, "cases": cases,
            "all_cases": len(cases), "valid_predecessor_cases": len(valid),
            "advantage_cases": len(advantage),
            "invalid_reason_counts": dict(collections.Counter(
                row["invalid_reason"] for row in cases if not row["valid_predecessor"])),
            "raw_source_to_matched_target_um": _summary(
                [row["raw_source_to_matched_target_um"] for row in cases]),
            "raw_source_to_occupant_um": _summary(
                [row["raw_source_to_occupant_um"] for row in cases]),
            "motion_to_matched_target_um": _summary(
                [row["motion_to_matched_target_um"] for row in valid]),
            "motion_to_occupant_um": _summary(
                [row["motion_to_occupant_um"] for row in valid]),
            "target_advantage_um": _summary([row["target_advantage_um"] for row in valid])}


def main():
    started = time.time()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert PRIOR_GEOMETRY["status"] == "PASS_EXP227_SOURCE10_ASSOCIATION_GEOMETRY_AUDIT"
    assert PRIOR_GEOMETRY["totals"]["unmatched_only_cases"] == 69
    assert PRIOR_GEOMETRY["totals"]["within_5um"] == 5
    assert PRIOR_GEOMETRY["totals"]["plausible_colocation_gate"] == "FAIL"
    # Replays all graph/input/evaluator hashes, official score and 87 case identities
    # before any motion aggregate. The source-only audit hook is installed there.
    baseline = geometry_main()
    for key in ("status", "source_score", "source_graph_gate", "rows", "totals",
                "inputs", "scorer_pins", "target6bba_access", "candidate_tuning"):
        assert baseline[key] == PRIOR_GEOMETRY[key], key
    assert baseline["source_score"] == SOURCE_SCORE
    from biohub_tracking.io import open_dataset
    from score_exp227_source_graph10 import gate

    config = json.loads((SCORER_CODE / "score_config.json").read_text())
    plan, graphs, gate_receipt = gate(config)
    assert tuple(row["dataset"] for row in plan["movies"]) == SOURCE_IDS
    assert gate_receipt["status"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"

    rows = []
    for name, previous in zip(SOURCE_IDS, baseline["rows"]):
        graph = graphs.pop(name)
        ds = open_dataset(DATA / (name + ".zarr"), require_tracks=True, load_image=False)
        row = _motion_movie(name, graph, ds.scale, previous)
        assert row["all_cases"] == previous["unmatched_only_cases"]
        rows.append(row)
        print(json.dumps({"done": name, "cases": row["all_cases"],
                          "valid": row["valid_predecessor_cases"],
                          "advantage": row["advantage_cases"]}),
              file=sys.stderr, flush=True)
        del graph, ds
        gc.collect()
    assert not graphs
    cases = [case for row in rows for case in row["cases"]]
    valid = [case for case in cases if case["valid_predecessor"]]
    advantage = [case for case in valid if case["target_advantage_at_least_2um"]]
    assert len(cases) == 69 and len({(case["dataset"], case["gt_source_id"])
                                     for case in cases}) == 69
    assert sum(row["valid_predecessor_cases"] for row in rows) == len(valid)
    assert sum(row["advantage_cases"] for row in rows) == len(advantage)
    movies_with_advantage = [row["dataset"] for row in rows if row["advantage_cases"]]
    gate_pass = len(advantage) >= 20 and len(movies_with_advantage) >= 4
    return {"status": "PASS_EXP227_SOURCE10_ASSOCIATION_VELOCITY_AUDIT",
            "source_score": SOURCE_SCORE, "source_graph_gate": gate_receipt["status"],
            "rows": rows,
            "totals": {"all_cases": len(cases), "valid_predecessor_cases": len(valid),
                       "advantage_cases": len(advantage),
                       "required_advantage_cases": 20,
                       "movies_with_advantage": movies_with_advantage,
                       "required_movies_with_advantage": 4,
                       "plausible_motion_gate": "PASS" if gate_pass else "FAIL",
                       "invalid_reason_counts": dict(collections.Counter(
                           case["invalid_reason"] for case in cases if not case["valid_predecessor"])),
                       "raw_source_to_matched_target_um": _summary(
                           [case["raw_source_to_matched_target_um"] for case in cases]),
                       "raw_source_to_occupant_um": _summary(
                           [case["raw_source_to_occupant_um"] for case in cases]),
                       "motion_to_matched_target_um": _summary(
                           [case["motion_to_matched_target_um"] for case in valid]),
                       "motion_to_occupant_um": _summary(
                           [case["motion_to_occupant_um"] for case in valid]),
                       "target_advantage_um": _summary(
                           [case["target_advantage_um"] for case in valid])},
            "inputs": baseline["inputs"], "scorer_pins": baseline["scorer_pins"],
            "elapsed_seconds": time.time() - started,
            "target6bba_access": False, "candidate_tuning": False,
            "limitations": ["Post hoc source-inner epoch10 training monitor, not target OOF.",
                            "Official matching is conditional on the fixed final graph.",
                            "Unmatched predicted occupants may represent real cells.",
                            "A distance ranking alone does not authorize rewiring or imply a score gain.",
                            "Cases cluster by movie and predecessor availability restricts the denominator."]}


if __name__ == "__main__":
    print(json.dumps(main(), allow_nan=False))
