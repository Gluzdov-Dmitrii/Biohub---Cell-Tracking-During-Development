"""Guarded CPU scorer for the new, sealed EXP209 175-graph reconstruction.

The historical EXP209 final CSV bytes were not retained.  This scores only the
new reconstruction, after an independent label-free rehash and source replay.
Nothing in this module opens GEFF until no_metric_gate.json is durable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import run_exp209_reconstruction_chunk_v1 as reconstruction
import verify_exp209_reconstruction_graphs_v1 as graph_verifier


RUN_NAME = "exp209_reconstructed_current_scorer_v1_20260927"
RECONSTRUCTION_NAME = graph_verifier.RUN_NAME
RECONSTRUCTION_BUNDLE_SHA = "cdf49fad597f1dcc47e65d841cc894ed2be439f45f4bfe1838e790b390c8a311"
RECONSTRUCTION_CONTRACT_SHA = "3860dce507c02b49386414a26c51071f6ff993e8b49476dc46e2b232973e8dd0"
RECONSTRUCTION_GATE_SHA = "8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1"
RECONSTRUCTION_RUNNER_SHA = "8bebdbdf27b94a254efe40d3d9db60241841c2b3c98370a765aee758b7f31597"
RECONSTRUCTION_VERIFIER_SHA = "2bf0b5cb536d76bab57bfddf3033b749a5af5871bfc8cb265d426b16a60f03d2"
HISTORICAL_RESULT_SHA = graph_verifier.HISTORICAL_RESULT_SHA
HISTORICAL_METRICS_SHA = "31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83"
HISTORICAL_DIVISION_SHA = "d1cf1e0a43009d02174f1699ce2aa28458a2220ac4b521731d3bcf31cf8c76be"
CURRENT_METRICS_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
CURRENT_DIVISION_SHA = "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"
CURRENT_INIT_SHA = "de33668aee4fd1822a11989b432a7ba6c4b36fd2993ec8f564a63d427cde05de"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
ORGANIZER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
HISTORICAL_SCORE = 0.6815218332750073
OLD_COUNT_FIELDS = ("edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
                    "division_fn", "num_pred_nodes")
OLD_FLOAT_FIELDS = ("node_recall", "total_node_ratio", "edge_jaccard", "adj_edge_jaccard")


class ScoreError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScoreError(message)


def sha(path: Path) -> str:
    return graph_verifier.sha256(Path(path))


def pinned(path: Path, digest: str, label: str) -> None:
    require(path.is_file() and sha(path) == digest, f"{label} missing or SHA mismatch: {path}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_bundle(bundle_dir: Path, expected_sha: str) -> dict:
    """Verify every bundled byte and reject extra files before any experiment read."""
    bundle_dir = bundle_dir.resolve()
    manifest_path = bundle_dir / "bundle_manifest.json"
    pinned(manifest_path, expected_sha, "scorer bundle manifest")
    manifest = load_json(manifest_path)
    require(manifest.get("experiment") == "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1",
            "scorer bundle experiment mismatch")
    rows = manifest.get("files")
    require(isinstance(rows, list) and rows, "empty scorer bundle manifest")
    names = [row.get("name") for row in rows]
    require(all(isinstance(name, str) and name and not Path(name).is_absolute() and
                ".." not in Path(name).parts and "\\" not in name for name in names),
            "unsafe scorer bundle filename")
    require(len(set(names)) == len(names), "duplicate scorer bundle filename")
    actual = {item.relative_to(bundle_dir).as_posix() for item in bundle_dir.rglob("*")
              if item.is_file() and "__pycache__" not in item.parts}
    require(actual == set(names) | {"bundle_manifest.json"}, "scorer bundle file set mismatch")
    for row in rows:
        file = bundle_dir / row["name"]
        require(file.is_file() and not file.is_symlink() and
                file.stat().st_size == row["bytes"] and sha(file) == row["sha256"],
                f"scorer bundle file mismatch: {row['name']}")
    require(sha(bundle_dir / "score_exp209_reconstructed_current_v1.py") ==
            sha(Path(__file__)), "executed scorer differs from sealed bundle")
    return manifest


def validate_reconstruction_bundle(code_dir: Path) -> None:
    pinned(code_dir / "bundle_manifest.json", RECONSTRUCTION_BUNDLE_SHA,
           "reconstruction bundle manifest")
    manifest = load_json(code_dir / "bundle_manifest.json")
    require(manifest.get("experiment") == graph_verifier.EXPERIMENT,
            "reconstruction bundle experiment mismatch")
    for row in manifest["files"]:
        path = code_dir / row["name"]
        require(path.is_file() and not path.is_symlink() and
                path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                f"reconstruction bundle file mismatch: {row['name']}")
    pinned(code_dir / "run_exp209_reconstruction_chunk_v1.py",
           RECONSTRUCTION_RUNNER_SHA, "reconstruction runner")
    pinned(code_dir / "verify_exp209_reconstruction_graphs_v1.py",
           RECONSTRUCTION_VERIFIER_SHA, "reconstruction verifier")
    pinned(Path(reconstruction.__file__), RECONSTRUCTION_RUNNER_SHA,
           "bundled reconstruction runner")
    pinned(Path(graph_verifier.__file__), RECONSTRUCTION_VERIFIER_SHA,
           "bundled reconstruction verifier")


def historical_selected_rows(historical: dict) -> tuple[list[str], dict[str, dict]]:
    ordered: list[str] = []
    reference: dict[str, dict] = {}
    for direction, prefix, count in (("forward", "6bba_", 116), ("reverse", "44b6_", 59)):
        rows = historical["directions"][direction]["selected_rows"]
        require(len(rows) == count, f"{direction} historical selected-row count mismatch")
        for row in rows:
            raw = row["dataset"]
            require(raw.endswith(".zarr"), "historical dataset suffix mismatch")
            name = raw[:-5]
            require(name.startswith(prefix) and name not in reference,
                    "historical dataset direction/uniqueness mismatch")
            copy = dict(row)
            copy["dataset"] = name
            require(set(copy) == {"dataset", *OLD_COUNT_FIELDS, *OLD_FLOAT_FIELDS},
                    f"historical row fields mismatch: {name}")
            ordered.append(name)
            reference[name] = copy
    require(len(ordered) == 175, "historical selected cohort incomplete")
    return ordered, reference


def compare_historical_row(actual: dict, expected: dict) -> None:
    """The check compares newly evaluated graphs to archived EXP209 values."""
    require(set(actual) == set(expected) and actual["dataset"] == expected["dataset"],
            "historical replay dataset/field mismatch")
    name = expected["dataset"]
    for key in OLD_COUNT_FIELDS:
        require(type(actual[key]) is int and actual[key] == expected[key],
                f"historical replay {name}/{key}: {actual[key]} != {expected[key]}")
    for key in OLD_FLOAT_FIELDS:
        got, want = float(actual[key]), float(expected[key])
        require(math.isfinite(got) and math.isfinite(want) and abs(got - want) <= 1e-12,
                f"historical replay {name}/{key}: {got} != {want}")


def compare_historical_summary(actual: dict, expected: dict) -> None:
    require(set(actual) == set(expected), "historical pooled summary field mismatch")
    for key, want in expected.items():
        got = actual[key]
        if key in (*OLD_COUNT_FIELDS, "n"):
            require(type(got) is int and got == want,
                    f"historical pooled {key}: {got} != {want}")
        else:
            got, want = float(got), float(want)
            require(math.isfinite(got) and math.isfinite(want) and
                    abs(got - want) <= 1e-12,
                    f"historical pooled {key}: {got} != {want}")


def comparable_historical_summary(summary: dict, rows: list[dict],
                                  archived_summary: dict) -> dict:
    """Match the EXP209 archive's pooled fields from the old metric output."""
    comparable = {key: summary[key] for key in archived_summary if key in summary}
    for key in ("edge_tp", "edge_fp", "edge_fn"):
        if key in archived_summary:
            comparable[key] = sum(row[key] for row in rows)
    return comparable


def graph_path(run_root: Path, chunk: dict, name: str) -> Path:
    return run_root / "chunks" / chunk["name"] / "output" / f"graph__{name}.csv"


def pinned_graph(csv_path: Path, expected: dict) -> None:
    receipt_path = csv_path.with_suffix(".receipt.json")
    require(sha(csv_path) == expected["csv_sha256"] and
            sha(receipt_path) == expected["receipt_sha256"],
            f"{expected['dataset']}: graph/receipt changed after no-metric gate")


def serialized_graph_sha(name: str, coords, edges) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(reconstruction.COLUMNS)
    writer.writerows(reconstruction.graph_rows(name, coords, edges))
    return hashlib.sha256(stream.getvalue().encode("utf-8")).hexdigest()


def source_telemetry_replay(contract: dict, manifest: dict, gate: dict,
                            run_root: Path) -> list[dict]:
    """Recompute frozen source functions and every canonical graph, no labels."""
    by_name = {row["dataset"]: row for row in gate["graph_hashes"]}
    require(len(by_name) == 175, "sealed graph map incomplete")
    historical = load_json(Path(contract["historical_result"]))
    _, reference = historical_selected_rows(historical)
    records = []
    for chunk in contract["chunks"]:
        for name in chunk["movies"]:
            image_sha = reconstruction.image_tree_sha256(
                Path(contract["data_root"]), name, reconstruction.image_entries(manifest, name))
            require(image_sha == by_name[name]["image_tree_sha256"],
                    f"{name}: actual image tree SHA differs from sealed graph")
            coords, edges, shape, cache_sha, gap_sha = reconstruction.reconstruct_one(
                contract, chunk, name, image_sha)
            expected = by_name[name]
            require(list(shape) == load_json(graph_path(run_root, chunk, name).with_suffix(
                ".receipt.json"))["shape"], f"{name}: shape differs from graph receipt")
            require(len(coords) == expected["nodes"] == reference[name]["num_pred_nodes"] and
                    len(edges) == expected["edges"], f"{name}: reconstructed graph count mismatch")
            reconstructed_sha = serialized_graph_sha(name, coords, edges)
            require(reconstructed_sha == expected["csv_sha256"] and
                    reconstructed_sha == sha(graph_path(run_root, chunk, name)),
                    f"{name}: reconstructed graph bytes differ from sealed CSV")
            records.append({"dataset": name, "direction": chunk["direction"],
                            "csv_sha256": reconstructed_sha,
                            "input_cache_sha256": cache_sha,
                            "gap_cache_sha256": gap_sha,
                            "image_tree_sha256": image_sha,
                            "historical_source_telemetry": "PASS"})
    require([row["dataset"] for row in records] == [row["dataset"] for row in gate["graph_hashes"]],
            "source telemetry replay order differs from sealed graph order")
    return records


def graph_gate(config: dict) -> tuple[dict, dict, list[str], dict[str, dict]]:
    """All checks here are label-free and execute before any metric import."""
    contract_path = Path(config["reconstruction_contract"])
    run_root = Path(config["reconstruction_run_root"])
    code_dir = Path(config["reconstruction_code_dir"])
    require(run_root.name == RECONSTRUCTION_NAME and
            code_dir.name == RECONSTRUCTION_NAME, "reconstruction namespace mismatch")
    pinned(contract_path, RECONSTRUCTION_CONTRACT_SHA, "reconstruction contract")
    pinned(run_root / "no_metric_gate.json", RECONSTRUCTION_GATE_SHA,
           "completed reconstruction no-metric gate")
    validate_reconstruction_bundle(code_dir)
    sealed = load_json(run_root / "no_metric_gate.json")
    independently_checked = graph_verifier.gate(contract_path, run_root)
    require(independently_checked == sealed, "independent full175 graph gate differs from durable gate")
    require(sealed["status"] == "PASS_EXP209_RECONSTRUCTION175_NO_METRIC_GATE" and
            sealed["labels_read"] is False and sealed["scientific_metrics_emitted"] is False,
            "reconstruction graph gate status/label fields mismatch")
    contract, historical, manifest = reconstruction.check_contract(contract_path)
    require(Path(contract["code_dir"]) == code_dir and
            Path(contract["run_root"]) == run_root,
            "scorer paths differ from pinned reconstruction contract")
    ordered, reference = historical_selected_rows(historical)
    require(ordered == [row["dataset"] for row in sealed["graph_hashes"]],
            "historical selected rows differ from reconstructed cohort")
    replay = source_telemetry_replay(contract, manifest, sealed, run_root)
    receipt = {"status": "PASS_EXP209_RECONSTRUCTED175_INDEPENDENT_NO_METRIC_GATE",
               "experiment": "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1",
               "reconstruction_gate_sha256": RECONSTRUCTION_GATE_SHA,
               "reconstruction_contract_sha256": RECONSTRUCTION_CONTRACT_SHA,
               "reconstruction_bundle_manifest_sha256": RECONSTRUCTION_BUNDLE_SHA,
               "historical_exp209_selected_rows_sha256": HISTORICAL_RESULT_SHA,
               "source_telemetry_replay": "PASS_ALL175",
               "movie_count": 175, "direction_counts": {"forward": 116, "reverse": 59},
               "chunk_count": 8, "labels_read": False, "scientific_metrics_emitted": False,
               "current_organizer_score": None,
               "sealed_graph_hashes": sealed["graph_hashes"],
               "reconstructed_source_records": replay,
               "control_hashes": sealed["control_hashes"]}
    return receipt, contract, ordered, reference


def image_scale(data_root: Path, name: str, shape: list[int]) -> tuple[float, float, float]:
    image = data_root / f"{name}.zarr"
    root = load_json(image / "zarr.json")
    array = load_json(image / "0" / "zarr.json")
    require(array["shape"] == shape, f"{name}: image shape changed after graph gate")
    transform = root["attributes"]["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]
    scale = tuple(float(value) for value in transform["scale"][1:])
    require(transform["type"] == "scale" and len(scale) == 3 and
            all(math.isfinite(value) and value > 0 for value in scale),
            f"{name}: invalid image scale")
    return scale


def load_label_dataset(data_root: Path, name: str, scale: tuple[float, float, float]):
    """The sole GEFF access function; call only after durable no_metric_gate."""
    import tracksdata as td
    from geff import GeffMetadata
    path = data_root / f"{name}.geff"
    loaded = td.graph.IndexedRXGraph.from_geff(path)
    gt = loaded[0] if isinstance(loaded, tuple) else loaded
    estimate = (GeffMetadata.read(path).extra or {}).get("estimated_number_of_nodes")
    require(estimate is not None and math.isfinite(float(estimate)) and float(estimate) > 0,
            f"{name}: missing estimated GT node count")
    return SimpleNamespace(tracks=gt, scale=scale), float(estimate)


def score_movie(name: str, csv_path: Path, dataset, estimate: float, metric_module) -> dict:
    from score_exp214_paired import read_graphs
    from score_exp223_official import score_one
    from score_current_metric_lightweight import build_graph
    graph = read_graphs(csv_path)
    require(set(graph) == {name}, f"{name}: graph parser found unexpected dataset")

    def evaluate(pred, gt, *, scale):
        return metric_module.evaluate(pred, gt, scale=scale, max_distance=7.0)

    return score_one(name, graph[name], dataset, estimate, evaluate,
                     metric_module.node_recall, metric_module.per_sample_metrics,
                     build_graph)


def metric_source_gate(bundle: Path) -> None:
    pinned(bundle / "legacy_official/metrics.py", HISTORICAL_METRICS_SHA,
           "historical EXP209 evaluator")
    pinned(bundle / "legacy_official/division_metrics.py", HISTORICAL_DIVISION_SHA,
           "historical EXP209 division evaluator")
    pinned(bundle / "current_official/__init__.py", CURRENT_INIT_SHA,
           "current organizer package")
    pinned(bundle / "current_official/metrics.py", CURRENT_METRICS_SHA,
           "current organizer evaluator")
    pinned(bundle / "current_official/division_metrics.py", CURRENT_DIVISION_SHA,
           "current organizer division evaluator")


def historical_replay(output: Path, contract: dict, ordered: list[str],
                      reference: dict[str, dict], bundle: Path) -> dict:
    """All 175 archived EXP209 rows must match before any current metric call."""
    import legacy_official.metrics as legacy
    from score_current_metric_lightweight import label_manifest
    data_root = Path(contract["data_root"])
    cohort = {name: {"zarr": str(data_root / f"{name}.zarr")} for name in ordered}
    labels = label_manifest(cohort, ordered)
    graph_map = {name: (chunk, graph_path(Path(contract["run_root"]), chunk, name))
                 for chunk in contract["chunks"] for name in chunk["movies"]}
    graph_hashes = {row["dataset"]: row for row in
                    load_json(output / "no_metric_gate.json")["sealed_graph_hashes"]}
    require(set(graph_hashes) == set(ordered), "historical replay graph SHA coverage mismatch")
    rows = []
    for name in ordered:
        chunk, path = graph_map[name]
        pinned_graph(path, graph_hashes[name])
        receipt = load_json(path.with_suffix(".receipt.json"))
        scale = image_scale(data_root, name, receipt["shape"])
        dataset, estimate = load_label_dataset(data_root, name, scale)
        row = score_movie(name, path, dataset, estimate, legacy)
        compare_historical_row(row, reference[name])
        rows.append(row)
        print(json.dumps({"historical_replay_movie": name}), flush=True)
    require(len(rows) == 175 and len({row["dataset"] for row in rows}) == 175,
            "historical replay did not cover 175 movies")
    summary = legacy.summarise(rows)
    archived_summary = load_json(Path(contract["historical_result"]))["combined"]["frozen_selected"]
    comparable_summary = comparable_historical_summary(summary, rows, archived_summary)
    compare_historical_summary(comparable_summary, archived_summary)
    require(math.isfinite(float(summary["score"])) and
            abs(float(summary["score"]) - HISTORICAL_SCORE) <= 1e-12,
            f"historical EXP209 pooled replay differs: {summary['score']}")
    require(label_manifest(cohort, ordered) == labels, "label tree changed during historical replay")
    result = {"status": "PASS_EXP209_RECONSTRUCTED_HISTORICAL175_REPLAY_1E12",
              "evidence_class": "behavioral replay of new reconstructed graphs; original final graph bytes absent",
              "archived_exp209_selected_rows_sha256": HISTORICAL_RESULT_SHA,
              "historical_metrics_sha256": HISTORICAL_METRICS_SHA,
              "historical_division_sha256": HISTORICAL_DIVISION_SHA,
              "archived_exp209_score": HISTORICAL_SCORE,
              "summary": summary, "archived_comparable_summary": comparable_summary,
              "rows": rows, "label_tree_hashes": labels,
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json")}
    graph_verifier.write_once_durable(output / "historical_replay.json", result)
    return result


def current_score(output: Path, contract: dict, ordered: list[str],
                  historical: dict, bundle: Path) -> dict:
    """Current metric is imported and executed only after replay receipt PASS."""
    require(historical["status"] == "PASS_EXP209_RECONSTRUCTED_HISTORICAL175_REPLAY_1E12" and
            load_json(output / "historical_replay.json") == historical,
            "historical replay durable receipt mismatch")
    from score_current_metric_lightweight import label_manifest, runtime_gate
    config = {"tracksdata_commit": TRACKSDATA_COMMIT,
              "current_metrics_sha256": CURRENT_METRICS_SHA,
              "current_division_sha256": CURRENT_DIVISION_SHA,
              "current_metrics": str(bundle / "current_official/metrics.py"),
              "current_division": str(bundle / "current_official/division_metrics.py")}
    runtime, synthetic = runtime_gate(config, CURRENT_METRICS_SHA, CURRENT_DIVISION_SHA)
    import current_official.metrics as current
    data_root = Path(contract["data_root"])
    graph_map = {name: graph_path(Path(contract["run_root"]), chunk, name)
                 for chunk in contract["chunks"] for name in chunk["movies"]}
    graph_hashes = {row["dataset"]: row for row in
                    load_json(output / "no_metric_gate.json")["sealed_graph_hashes"]}
    require(set(graph_hashes) == set(ordered), "current scorer graph SHA coverage mismatch")
    rows = []
    for name in ordered:
        path = graph_map[name]
        pinned_graph(path, graph_hashes[name])
        receipt = load_json(path.with_suffix(".receipt.json"))
        scale = image_scale(data_root, name, receipt["shape"])
        dataset, estimate = load_label_dataset(data_root, name, scale)
        row = score_movie(name, path, dataset, estimate, current)
        require(row["num_pred_nodes"] == graph_hashes[name]["nodes"],
                f"{name}: current metric node count differs from sealed graph")
        rows.append(row)
        print(json.dumps({"current_metric_movie": name}), flush=True)
    summary = current.summarise(rows)
    require(summary["n"] == 175 and math.isfinite(float(summary["score"])),
            "current organizer summary invalid")
    cohort = {name: {"zarr": str(data_root / f"{name}.zarr")} for name in ordered}
    require(label_manifest(cohort, ordered) == historical["label_tree_hashes"],
            "label tree changed after historical replay")
    result = {"status": "PASS_EXP209_RECONSTRUCTED175_CURRENT_ORGANIZER_V1",
              "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
              "graph_identity": "new reconstructed graphs; original final graph byte identity unavailable",
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "historical_replay_sha256": sha(output / "historical_replay.json"),
              "historical_replay": "PASS_ALL175_FIELDS_AND_POOLED_SCORE_1E12",
              "metric_repo_commit": ORGANIZER_COMMIT,
              "current_metrics_sha256": CURRENT_METRICS_SHA,
              "current_division_sha256": CURRENT_DIVISION_SHA,
              "tracksdata_commit": TRACKSDATA_COMMIT,
              "runtime": runtime, "synthetic_contract": synthetic,
              "summary": summary, "rows": rows,
              "labels_read_only_after_durable_no_metric_gate": True}
    graph_verifier.write_once_durable(output / "result.json", result)
    return result


def run(config_path: Path, config_sha: str, manifest_sha: str) -> dict:
    bundle = Path(__file__).resolve().parent
    validate_bundle(bundle, manifest_sha)
    pinned(config_path, config_sha, "scorer config")
    config = load_json(config_path)
    require(config_path.resolve() == (bundle / "config.json").resolve(),
            "scorer config must be inside sealed bundle")
    require(config.get("experiment") == "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1" and
            Path(config.get("scorer_code_dir", "")).resolve() == bundle and
            config.get("reconstruction_gate_sha256") == RECONSTRUCTION_GATE_SHA and
            config.get("reconstruction_bundle_manifest_sha256") == RECONSTRUCTION_BUNDLE_SHA and
            config.get("reconstruction_contract_sha256") == RECONSTRUCTION_CONTRACT_SHA and
            config.get("current_metrics_sha256") == CURRENT_METRICS_SHA and
            config.get("current_division_sha256") == CURRENT_DIVISION_SHA and
            config.get("metric_repo_commit") == ORGANIZER_COMMIT and
            config.get("tracksdata_commit") == TRACKSDATA_COMMIT,
            "scorer config provenance mismatch")
    output = Path(config["output"])
    require(output.name == RUN_NAME and not output.exists() and output.parent.is_dir(),
            "scorer output must be new fixed run namespace")
    metric_source_gate(bundle)
    # This audit boundary guards accidental GEFF use by the graph and source gates.
    label_access = {"allowed": False}

    def audit(event, args):
        if label_access["allowed"] or event not in {
                "open", "os.listdir", "os.scandir", "os.stat", "os.remove", "os.rename"} or not args:
            return
        raw = args[0]
        if isinstance(raw, (str, bytes, os.PathLike)):
            if any(part.lower().endswith(".geff") for part in Path(os.fsdecode(raw)).parts):
                raise PermissionError("EXP209 scorer forbids GEFF before durable graph gate")

    sys.addaudithook(audit)
    receipt, contract, ordered, reference = graph_gate(config)
    from check_current_organizer_metric_runtime import validate_runtime
    receipt["isolated_runtime_metadata"] = validate_runtime("remote_py311")
    output.mkdir(parents=False, exist_ok=False)
    graph_verifier.write_once_durable(output / "no_metric_gate.json", receipt)
    require(load_json(output / "no_metric_gate.json") == receipt,
            "durable no-metric gate reread mismatch")
    label_access["allowed"] = True
    try:
        replay = historical_replay(output, contract, ordered, reference, bundle)
    except Exception as exc:
        graph_verifier.write_once_durable(output / "historical_replay_failure.json",
            {"status": "BLOCKED_EXP209_RECONSTRUCTED_HISTORICAL_REPLAY",
             "reason": f"{type(exc).__name__}: {exc}",
             "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
             "current_metric_executed": False})
        raise
    return current_score(output, contract, ordered, replay, bundle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--bundle-manifest-sha256", required=True)
    args = parser.parse_args()
    result = run(args.config, args.config_sha256, args.bundle_manifest_sha256)
    print(json.dumps({"status": result["status"], "score": result["summary"]["score"]}))


if __name__ == "__main__":
    main()
