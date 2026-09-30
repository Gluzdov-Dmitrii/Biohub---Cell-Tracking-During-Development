"""Official 175-movie EXP228 diagnostic after all no-label shards are sealed."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, must_sha, released, rows_close, score_one


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_graph(path, name, shape):
    graphs = read_graphs(path)
    assert set(graphs) == {name}
    graph = graphs[name]
    for point in graph["nodes"].values():
        assert all(float(v) == int(v) and 0 <= v < limit for v, limit in zip(point, shape))
    return graph


def gate(config):
    code = Path(config["inference_code"])
    must_sha(code / "code_manifest.json", config["inference_manifest_sha256"], "EXP228 code manifest")
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        target = (code / name).resolve()
        assert target.is_relative_to(code.resolve())
        must_sha(target, digest, "EXP228 staged file")
    must_sha(config["reference_manifest"], config["reference_manifest_sha256"], "EXP223 reference manifest")
    must_sha(config["cohort"], config["cohort_sha256"], "175 movie cohort")
    cohort = json.loads(Path(config["cohort"]).read_text())["rows"]
    cmap = {r["dataset"]: r for r in cohort}
    assert len(cmap) == len(cohort) == 175
    assert sum(name.startswith("44b6_") for name in cmap) == 59
    assert sum(name.startswith("6bba_") for name in cmap) == 116
    assert all(r["fold"] == (0 if r["dataset"].startswith("44b6_") else 1) for r in cohort)
    refs = json.loads(Path(config["reference_manifest"]).read_text())
    assert refs["cohort_sha256"] == config["cohort_sha256"]
    ref = {r["dataset"]: r for r in refs["rows"]}
    assert len(ref) == 175 and set(ref) == set(cmap)
    for name, record in ref.items():
        assert record["shape"] == cmap[name]["shape"]
        assert sha(record["reference_csv"]) == record["reference_sha256"]
        assert sha(record["receipt_path"]) == record["receipt_sha256"]
        receipt = json.loads(Path(record["receipt_path"]).read_text())
        assert receipt["contract"]["dataset"] == name
        assert receipt["contract"]["arm"] == "selected50_20"
        assert receipt["contract"]["fold"] == cmap[name]["fold"]
        assert receipt["csv_sha256"] == record["reference_sha256"]
        checked_graph(record["reference_csv"], name, record["shape"])
    new = {}
    plan_hashes = []
    for chunk in range(8):
        plan_path = code / (f"plan_chunk{chunk:02d}.json")
        plan_sha = sha(plan_path)
        plan = json.loads(plan_path.read_text())
        assert plan["experiment"] == "EXP228" and plan["chunk"] == chunk
        assert plan["chunk_count"] == 8 and plan["mode"] == "heldout_same_fold_ensemble"
        assert plan["cohort_sha256"] == config["cohort_sha256"]
        assert plan["mixture"] == [0.5, 0.5]
        run = Path(plan["output"]).parent
        ok, _ = released(run)
        assert ok, f"chunk{chunk:02d} not released"
        output = run / "output"
        complete = json.loads((output / "complete.json").read_text())
        assert complete["status"] == "PASS_EXP228_NO_LABEL_CHUNK"
        assert complete["chunk"] == chunk and complete["no_target_labels"] is True
        assert complete["n_movies"] == len(plan["rows"]) == len(complete["records"])
        assert [r["dataset"] for r in complete["records"]] == [r["dataset"] for r in plan["rows"]]
        expected_files = {"complete.json"}
        for row, receipt in zip(plan["rows"], complete["records"]):
            name = row["dataset"]
            assert name.startswith("6bba_") and name not in new
            assert row["fold"] == receipt["fold"] == 1
            assert row["shape"] == receipt["shape"] == cmap[name]["shape"]
            assert receipt["mixture"] == [0.5, 0.5]
            assert receipt["plan_sha256"] == plan_sha
            assert receipt["weights"] == plan["weights"]
            path = output / ("ensemble__" + name + ".csv")
            receipt_path = output / ("ensemble__" + name + ".json")
            assert Path(receipt["csv"]).resolve() == path.resolve()
            assert sha(path) == receipt["csv_sha256"]
            assert json.loads(receipt_path.read_text()) == receipt
            checked_graph(path, name, row["shape"])
            new[name] = {"csv": str(path), "sha256": receipt["csv_sha256"],
                         "plan_sha256": plan_sha, "chunk": chunk}
            expected_files.update((path.name, receipt_path.name))
        assert {p.name for p in output.iterdir()} == expected_files
        plan_hashes.append({"chunk": chunk, "sha256": plan_sha,
                            "complete_sha256": sha(output / "complete.json")})
    assert len(new) == 116 and set(new) == {name for name in cmap if name.startswith("6bba_")}
    gate_receipt = {"status": "PASS_EXP228_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS",
                    "reference_movies": 175, "new_6bba_movies": 116,
                    "cohort_sha256": config["cohort_sha256"],
                    "reference_manifest_sha256": config["reference_manifest_sha256"],
                    "plan_hashes": plan_hashes,
                    "new_csv_hashes": new,
                    "evidence_class": "target-selected Horaz diagnostic, not honest OOF"}
    return cmap, ref, new, gate_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.config) == args.config_sha256
    config = json.loads(args.config.read_text())
    assert config["experiment"] == "EXP228_OFFICIAL_SCORE175"
    cmap, reference, new, gate_receipt = gate(config)
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "no_metric_gate.json").write_text(json.dumps(gate_receipt, indent=2) + "\n")

    must_sha(config["exp223_result"], config["exp223_result_sha256"], "EXP223 official result")
    old = json.loads(Path(config["exp223_result"]).read_text())
    assert old["status"] == "PASS_EXP223_OFFICIAL_BOTH_ARMS"
    old_rows = {r["dataset"]: r for r in old["rows"]["selected50_20"]}
    assert len(old_rows) == 175 and set(old_rows) == set(cmap)
    old_config = json.loads(Path(config["exp223_config"]).read_text())
    evaluator_pins(old_config)
    sys.path[:0] = [str(Path(config["repo"]) / "src"), str(Path(config["repo"]) / "scripts")]
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    baseline_rows, candidate_rows = [], []
    for name in sorted(cmap):
        movie = cmap[name]
        dataset = open_dataset(movie["zarr"], require_tracks=True, load_image=False)
        estimate = (GeffMetadata.read(Path(config["data_dir"]) / (name + ".geff")).extra or {}).get("estimated_number_of_nodes")
        assert estimate is not None and float(estimate) > 0
        ref_graph = checked_graph(reference[name]["reference_csv"], name, movie["shape"])
        baseline = score_one(name, ref_graph, dataset, estimate, evaluate, node_recall, per_sample_metrics, build_graph)
        rows_close(baseline, old_rows[name], tol=1e-12)
        baseline_rows.append(baseline)
        if name in new:
            graph = checked_graph(new[name]["csv"], name, movie["shape"])
            candidate = score_one(name, graph, dataset, estimate, evaluate, node_recall, per_sample_metrics, build_graph)
        else:
            candidate = dict(baseline)
        candidate_rows.append(candidate)
    baseline_summary = summarise(baseline_rows)
    rows_close(baseline_summary, old["summary"]["selected50_20"], tol=1e-12)
    candidate_summary = summarise(candidate_rows)
    by_embryo = {prefix: summarise([r for r in candidate_rows if r["dataset"].startswith(prefix + "_")])
                 for prefix in ("44b6", "6bba")}
    result = {"status": "PASS_EXP228_DIAGNOSTIC_OFFICIAL175",
              "evidence_class": "target-selected Horaz development diagnostic; not honest OOF",
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "baseline_replay": "PASS_1e-12", "baseline_summary": baseline_summary,
              "candidate_summary": candidate_summary, "candidate_by_embryo": by_embryo,
              "delta_vs_selected": candidate_summary["score"] - baseline_summary["score"],
              "rows": candidate_rows}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "score": candidate_summary["score"],
                      "delta": result["delta_vs_selected"]}))


if __name__ == "__main__":
    main()
