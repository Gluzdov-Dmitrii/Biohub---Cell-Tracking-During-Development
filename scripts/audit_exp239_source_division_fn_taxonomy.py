"""EXP239: source-only, post hoc division-FN taxonomy of frozen epoch-10 graphs.

This source is sealed into a separate local bundle. The remote execution path
is deliberately absent from preparation; it reads source GEFF only after an
fsynced 19-graph no-label gate. It never opens reciprocal target labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import sys


ROOT = Path("/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development")
DATA = ROOT / "data/exp213_source_view_20260912"
PACKAGE = Path(__file__).resolve().parent
OUTPUT = ROOT / "runs/exp239_source_division_fn_taxonomy_v1_20260927/output"
EXPECTED_PYTHON = ROOT / "envs/current-organizer-py311-e13cf-v1/bin/python"
IMAGE_AUDIT_SHA = "d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6"
METRIC_SHAS = {
    "tracking_cellmot_official/__init__.py": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    "tracking_cellmot_official/metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "tracking_cellmot_official/division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
STAGES = (
    "no_parent_side_match",
    "fewer_than_two_daughter_lineages",
    "no_local_fork",
    "directed_branch_failure",
    "organizer_veto_or_pairing",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(root: Path) -> tuple[str, int]:
    files = sorted((p for p in root.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(root).as_posix())
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" +
                      sha(path).encode() + b"\n")
    return digest.hexdigest(), len(files)


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def label_audit_hook(allowed: set[str], state: dict[str, bool]):
    roots = {(DATA / (name + ".geff")).resolve() for name in allowed}

    def guard(event, args):
        if event not in ("open", "os.listdir", "os.scandir") or not args:
            return
        raw = args[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.endswith(".geff") for part in path.parts):
            if not state["label_access_enabled"]:
                raise PermissionError("EXP239 source labels remain sealed before no-label gate")
            if not any(path.is_relative_to(root) for root in roots):
                raise PermissionError(f"EXP239 forbids GEFF outside source19: {path}")

    return guard


def verify_bundle(expected_sha: str) -> dict:
    manifest_path = PACKAGE / "manifest.json"
    assert sha(manifest_path) == expected_sha
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "SEALED_EXP239_LOCAL_ONLY"
    for relative, digest in manifest["files"].items():
        path = (PACKAGE / relative).resolve()
        assert path.is_relative_to(PACKAGE) and sha(path) == digest, relative
    for relative, digest in METRIC_SHAS.items():
        assert manifest["files"][relative] == digest
    return manifest


def validate_config(config: dict) -> list[str]:
    assert config["status"] == "PREREGISTERED_EXP239_SOURCE_DIVISION_FN_TAXONOMY"
    assert config["output"] == OUTPUT.as_posix()
    assert config["organizer_commit"] == "075fc5f5a52d11077f9dc2b074644618f26939e2"
    assert config["tracksdata_commit"] == "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
    assert config["source19_image_receipt_sha256"] == IMAGE_AUDIT_SHA
    cohorts = config["cohorts"]
    assert [row["experiment"] for row in cohorts] == ["EXP227", "EXP236"]
    assert [(row["source_embryo"], len(row["ids"])) for row in cohorts] == [
        ("44b6", 8), ("6bba", 11)]
    assert [row["expected_division_counts"] for row in cohorts] == [
        {"tp": 2, "fp": 6, "fn": 3}, {"tp": 1, "fp": 9, "fn": 8}]
    names = [name for cohort in cohorts for name in cohort["ids"]]
    assert len(names) == len(set(names)) == 19
    assert all(name.startswith(cohort["source_embryo"] + "_")
               for cohort in cohorts for name in cohort["ids"])
    assert all([row["dataset"] for row in cohort["graph_hashes"]] == cohort["ids"]
               for cohort in cohorts)
    return names


def to_graph(parsed: dict):
    import polars as pl
    import tracksdata as td

    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, -999999.0)
    original_ids = sorted(parsed["nodes"])
    ids = graph.bulk_add_nodes([
        {"t": int(parsed["nodes"][node_id][0]),
         "z": float(parsed["nodes"][node_id][1]),
         "y": float(parsed["nodes"][node_id][2]),
         "x": float(parsed["nodes"][node_id][3])}
        for node_id in original_ids])
    index = {node_id: offset for offset, node_id in enumerate(original_ids)}
    if parsed["edges"]:
        graph.add_edge_attr_key("edge_prob", pl.Float64, 0.0)
        graph.add_edge_attr_key("edge_dist", pl.Float64, 0.0)
        graph.bulk_add_edges([
            {"source_id": ids[index[source]], "target_id": ids[index[target]],
             "edge_prob": 1.0, "edge_dist": 0.0}
            for source, target in parsed["edges"]])
    return graph


def classify_window(pred, gt_div, divider_id: int, node_to_gt: dict[int, int],
                    invalid_forks: set[int], is_tp: bool, strong_fn) -> dict:
    """Classify one organizer-matched GT division window in fixed priority order."""
    gt_children = list(gt_div.successors(divider_id))
    assert len(gt_children) >= 2
    parent_side = {divider_id, *gt_div.predecessors(divider_id)}
    parents = {pred_id for pred_id, gt_id in node_to_gt.items()
               if gt_id in parent_side}
    daughters = [
        {pred_id for pred_id, gt_id in node_to_gt.items()
         if gt_id in {child, *gt_div.successors(child)}}
        for child in gt_children]
    represented = sum(bool(nodes) for nodes in daughters)
    local_nodes = parents | {successor for parent in parents
                             for successor in pred.successors(parent)}
    local_forks = {node for node in local_nodes if pred.out_degree(node) >= 2}
    strong_forks = {node for node in local_forks
                    if strong_fn(pred, node, parents, daughters)}
    valid_forks = strong_forks - invalid_forks
    if is_tp:
        assert valid_forks, "Organizer TP has no valid local fork"
        stage, subtype = "recovered", None
    elif not parents:
        stage, subtype = STAGES[0], None
    elif represented < 2:
        stage, subtype = STAGES[1], None
    elif not local_forks:
        stage, subtype = STAGES[2], None
    elif not strong_forks:
        stage, subtype = STAGES[3], None
    else:
        stage = STAGES[4]
        subtype = "bipartite_collision" if valid_forks else "organizer_invalid_fork"
    return {
        "category": stage, "subtype": subtype,
        "matched_parent_side_nodes": len(parents),
        "represented_daughter_lineages": represented,
        "local_forks": len(local_forks),
        "directed_forks": len(strong_forks),
        "valid_forks": len(valid_forks),
        "valid_fork_ids": valid_forks,
    }


def classify_all_divisions(pred, gt, division, scale: tuple[float, ...]) -> tuple[list[dict], dict]:
    """Use the pinned organizer matches, vetoes and pairing as the oracle."""
    import tracksdata as td

    official = division.score_divisions(pred, gt, scale=scale, max_distance=7.0)
    gt_divisions = division.extract_divisions(gt)
    matched = division.match_divisions(pred, gt, scale=scale, max_distance=7.0)
    assert list(gt_divisions) == list(matched) == list(official.scores)
    _, cross_component, malformed = division._pred_division_fork_sets(
        pred, gt, scale, 7.0)
    invalid = cross_component | malformed
    candidates = {}
    events = []
    keys = td.DEFAULT_ATTR_KEYS
    for divider_id, matched_pred in matched.items():
        attrs = division._matched_node_attrs(matched_pred)
        node_to_gt = {
            int(row[keys.NODE_ID]): int(row[keys.MATCHED_NODE_ID])
            for row in attrs.iter_rows(named=True)}
        event = classify_window(
            matched_pred, gt_divisions[divider_id], divider_id,
            node_to_gt, invalid, bool(official.scores[divider_id]),
            division._is_strongly_connected_division)
        grouped = division._matched_division_nodes(attrs, gt_divisions[divider_id], divider_id)
        if grouped is None:
            assert event["matched_parent_side_nodes"] == 0 or event["represented_daughter_lineages"] < 2
        else:
            parents, daughters = grouped
            assert len(parents) == event["matched_parent_side_nodes"]
            assert sum(bool(x) for x in daughters) == event["represented_daughter_lineages"]
        candidates[divider_id] = event.pop("valid_fork_ids")
        events.append({"gt_divider_id": int(divider_id), **event})
    pairing = division._bipartite_max_matching(list(candidates), candidates)
    assert {key: int(key in pairing) for key in candidates} == official.scores
    assert set(pairing.values()) == official.tp_forks
    counts = {"tp": sum(official.scores.values()), "fp": len(official.fp_forks),
              "fn": len(official.scores) - sum(official.scores.values())}
    assert sum(event["category"] != "recovered" for event in events) == counts["fn"]
    return events, counts


def graph_gate(config: dict):
    from check_current_organizer_metric_runtime import (
        load_metric, synthetic_contract, validate_runtime)

    assert Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()
    assert sys.prefix != sys.base_prefix
    runtime = validate_runtime("remote_py311")
    metric = load_metric(PACKAGE)
    contract = synthetic_contract(metric)
    assert contract["status"] == "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"
    image_path = PACKAGE / "source_inner19_image_scale_audit_v2_20260927.json"
    assert sha(image_path) == IMAGE_AUDIT_SHA
    image_audit = json.loads(image_path.read_text(encoding="utf-8"))
    assert image_audit["status"] == "PASS_SOURCE_INNER_EXACT19_IMAGE_SCALE_NO_LABELS"
    assert image_audit["count"] == len(image_audit["rows"]) == 19
    assert image_audit["source_labels_read"] is False
    assert image_audit["reciprocal_target_labels_read"] is False
    images = {row["dataset"]: row for row in image_audit["rows"]}
    assert list(images) == [name for cohort in config["cohorts"] for name in cohort["ids"]]
    for cohort in config["cohorts"]:
        for name in cohort["ids"]:
            row = images[name]
            assert row["scale"] == [1.625, 0.40625, 0.40625]
            zarr = DATA / (name + ".zarr")
            assert sha(zarr / "zarr.json") == row["zarr_root_sha256"]
            assert sha(zarr / "0/zarr.json") == row["zarr_array_sha256"]

    gated = []
    for cohort in config["cohorts"]:
        code = Path(cohort["scorer_code"])
        run = Path(cohort["scorer_run"])
        assert sha(code / "code_manifest.json") == cohort["scorer_manifest_sha256"]
        for relative, digest in json.loads((code / "code_manifest.json").read_text()).items():
            path = (code / relative).resolve()
            assert path.is_relative_to(code.resolve()) and sha(path) == digest
        assert sha(code / "score_config.json") == cohort["scorer_config_sha256"]
        scorer_config = json.loads((code / "score_config.json").read_text())
        assert scorer_config["data_dir"] == str(DATA)
        assert scorer_config["inference_run"] == cohort["graph_run"]
        assert scorer_config["checkpoint_sha256"] == cohort["checkpoint_sha256"]
        sys.path.insert(0, str(code))
        try:
            if cohort["experiment"] == "EXP227":
                from score_exp227_source_graph10 import gate
            else:
                from score_exp236_source_graph10 import gate
            plan, graphs, fresh_gate = gate(scorer_config)
        finally:
            sys.path.pop(0)
        assert tuple(row["dataset"] for row in plan["movies"]) == tuple(cohort["ids"])
        assert len(graphs) == len(cohort["ids"])
        assert fresh_gate["hashes"] == cohort["graph_hashes"]
        prior_gate = run / "output/no_metric_gate.json"
        assert sha(prior_gate) == cohort["score_gate_sha256"]
        assert json.loads(prior_gate.read_text()) == fresh_gate
        gated.append((cohort, graphs, fresh_gate))
    assert sum(len(graphs) for _, graphs, _ in gated) == 19
    return metric, runtime, contract, images, gated


def audit_cohort(cohort: dict, graphs: dict, images: dict, division) -> dict:
    import tracksdata as td

    movies = []
    label_hashes = []
    totals = Counter()
    for name in cohort["ids"]:
        label = DATA / (name + ".geff")
        before, file_count = tree_sha(label)
        assert file_count > 0
        pinned = cohort["geff_tree_hashes"].get(name)
        if pinned is not None:
            assert before == pinned, name
        loaded = td.graph.IndexedRXGraph.from_geff(label)
        gt = loaded[0] if isinstance(loaded, tuple) else loaded
        pred = to_graph(graphs[name])
        events, counts = classify_all_divisions(
            pred, gt, division, tuple(images[name]["scale"]))
        assert tree_sha(label) == (before, file_count), name
        label_hashes.append({"dataset": name, "tree_sha256": before,
                             "files": file_count, "previously_pinned": pinned is not None})
        categories = Counter(event["category"] for event in events)
        assert categories["recovered"] == counts["tp"]
        assert sum(categories[stage] for stage in STAGES) == counts["fn"]
        for key, value in counts.items():
            totals[key] += value
        movies.append({"dataset": name, "counts": counts,
                       "category_counts": {key: categories[key] for key in ("recovered", *STAGES)},
                       "events": [{"dataset": name, **event} for event in events]})
        print(json.dumps({"completed_source_movie": name, "gt_divisions": len(events)}),
              file=sys.stderr, flush=True)
    assert dict(totals) == cohort["expected_division_counts"]
    expected_events = 5 if cohort["experiment"] == "EXP227" else 9
    assert totals["tp"] + totals["fn"] == expected_events
    categories = Counter(event["category"] for row in movies for event in row["events"])
    assert categories["recovered"] == totals["tp"]
    assert sum(categories[stage] for stage in STAGES) == totals["fn"]
    return {"experiment": cohort["experiment"], "source_embryo": cohort["source_embryo"],
            "counts": dict(totals),
            "category_counts": {key: categories[key] for key in ("recovered", *STAGES)},
            "label_hashes": label_hashes, "movies": movies}


def main() -> None:
    import resource
    from check_current_organizer_metric_runtime import TRACKSDATA_COMMIT

    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert all(os.environ.get(key) == "4" for key in (
        "POLARS_MAX_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"))
    os.sched_setaffinity(0, {24, 25, 26, 27})
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (2400, 2400))
    signal.alarm(2700)
    manifest = verify_bundle(args.bundle_sha256)
    config = json.loads((PACKAGE / "config.json").read_text(encoding="utf-8"))
    names = validate_config(config)
    assert TRACKSDATA_COMMIT == config["tracksdata_commit"]
    assert not OUTPUT.exists(), "EXP239 output already exists; reconcile, never overwrite"
    state = {"label_access_enabled": False}
    sys.addaudithook(label_audit_hook(set(names), state))
    metric, runtime, contract, images, gated = graph_gate(config)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    no_label = {
        "status": "PASS_EXP239_SOURCE19_GRAPH_METRIC_GATE_BEFORE_LABEL_ACCESS",
        "bundle_sha256": args.bundle_sha256,
        "manifest": manifest,
        "runtime": runtime,
        "synthetic_contract": contract,
        "cohorts": [{"experiment": cohort["experiment"], "ids": cohort["ids"],
                     "graph_hashes": gate["hashes"],
                     "prior_no_metric_gate_sha256": cohort["score_gate_sha256"]}
                    for cohort, _, gate in gated],
        "reciprocal_target_labels_read": False,
    }
    atomic_json(OUTPUT / "no_label_gate.json", no_label)
    state["label_access_enabled"] = True
    import tracking_cellmot_official.division_metrics as division
    cohorts = [audit_cohort(cohort, graphs, images, division)
               for cohort, graphs, _ in gated]
    total_events = sum(sum(len(row["events"]) for row in cohort["movies"])
                       for cohort in cohorts)
    assert total_events == 14
    assert sum(cohort["counts"]["fn"] for cohort in cohorts) == 11
    result = {
        "status": "PASS_EXP239_SOURCE19_DIVISION_FN_TAXONOMY",
        "evidence_class": "post hoc source-inner training monitor; no threshold selection or promotion",
        "no_label_gate_sha256": sha(OUTPUT / "no_label_gate.json"),
        "organizer_commit": config["organizer_commit"],
        "metric_shas": METRIC_SHAS,
        "source_division_events": total_events,
        "source_division_fns": 11,
        "cohorts": cohorts,
        "reciprocal_target_labels_read": False,
        "gpu_used": False,
        "kaggle_post": False,
    }
    atomic_json(OUTPUT / "result.json", result)
    print(json.dumps({"status": result["status"],
                      "result_sha256": sha(OUTPUT / "result.json")}), flush=True)


if __name__ == "__main__":
    main()
