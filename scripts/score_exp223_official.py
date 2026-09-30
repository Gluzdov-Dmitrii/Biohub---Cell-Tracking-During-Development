#!/usr/bin/env python3
"""EXP223: official metrics for Horaz 175x2 after gating all 350 CSVs. No author custom metric.

No ensemble, no target-driven selection/training/queue/timer/submission.
Author 199 claim is not compared. development-adapted n=2 remains.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
ARMS = ("selected50_20", "fixedlast50_same_decoder")
CK = ("arm", "dataset", "fold", "mode", "weight_sha256", "manifest_sha256", "decoder_sha256", "code_sha256")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def must_sha(path, expected, label):
    got = sha(path)
    if got != expected:
        raise SystemExit("%s sha mismatch: %s != %s" % (label, got, expected))
    return got


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fold_of(ds):
    if ds.startswith("44b6_"):
        return 0
    if ds.startswith("6bba_"):
        return 1
    raise SystemExit("unmapped dataset %s" % ds)


def released(run):
    root = Path(run)
    ex = json.loads((root / "exit.json").read_text())
    sup = json.loads((root / "supervision/complete.json").read_text())
    control = json.loads((root / "supervision/control.json").read_text())
    ok = (ex["returncode"] == 0 and ex["hard_timeout"] is False
          and sup["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
          and sup["exit"] == ex and control["action"] == "release"
          and control["queue"]["state"] == "RELEASED"
          and Path(control["queue"]["run_path"]).resolve() == root.resolve())
    return ok, {"exit": ex, "supervision": sup, "control": control}


def evaluator_pins(cfg):
    pins = cfg["evaluator_files"]
    repo = Path(cfg["repo_path"])
    required = [repo / "src/biohub_tracking/metrics.py", repo / "src/biohub_tracking/io.py",
                repo / "scripts/predict_unet_transformer.py"]
    if any(str(p) not in pins for p in required):
        raise SystemExit("missing required evaluator pins")
    for path, digest in pins.items():
        must_sha(path, digest, "official evaluator")


def rows_close(got, exp, tol=1e-12):
    for k, v in exp.items():
        if k not in got:
            raise SystemExit("missing field %s" % k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if not np.isclose(float(got[k]), float(v), rtol=0, atol=tol, equal_nan=True):
                raise SystemExit("baseline replay %s: %s != %s" % (k, got[k], v))
        elif got[k] != v:
            raise SystemExit("baseline replay %s mismatch" % k)


def plan_movies(plan):
    out = []
    for m in plan["movies"]:
        out.append(m if isinstance(m, str) else m["dataset"])
    return out


def plan_arm_names(plan):
    arms = plan["arms"]
    if not arms:
        raise SystemExit("plan missing arms")
    if isinstance(arms[0], str):
        return list(arms)
    return [a.get("arm") or a.get("name") for a in arms]


def decl(plan, key, arm):
    v = plan.get(key)
    if isinstance(v, dict):
        return v.get(arm) or v.get(key)
    return v


def gate_all(cfg, analyze):
    must_sha(cfg["rollout_path"], cfg["rollout_sha256"], "rollout")
    must_sha(cfg["cohort_path"], cfg["cohort_sha256"], "cohort")
    rollout = json.loads(Path(cfg["rollout_path"]).read_text(encoding="utf-8"))
    cohort = json.loads(Path(cfg["cohort_path"]).read_text(encoding="utf-8"))
    rows = cohort["rows"] if isinstance(cohort, dict) and "rows" in cohort else cohort
    cmap = {r["dataset"]: r for r in rows}
    if len(rows) != 175 or len(cmap) != 175:
        raise SystemExit("cohort %s != 175" % len(cmap))
    for ds, r in cmap.items():
        if int(r["fold"]) != fold_of(ds):
            raise SystemExit("heldout map fail %s" % ds)
    code = Path(cfg["code_path"])
    must_sha(code / "code_manifest.json", cfg["code_manifest_sha256"], "code manifest")
    code_files = json.loads((code / "code_manifest.json").read_text())
    for name, digest in code_files.items():
        target = (code / name).resolve()
        if not target.is_relative_to(code.resolve()):
            raise SystemExit("code path traversal")
        must_sha(target, digest, "immutable source/weight")
    decoder = sha(code / "selected/resolved_config.json")
    weights = {a: {f: sha(code / folder / ("fold%d_%s.pt" % (f, suffix))) for f in (0, 1)}
               for a, folder, suffix in [(ARMS[0], "selected", "selected"), (ARMS[1], "fixed_last", "last")]}
    if len(rollout["chunks"]) != 8:
        raise SystemExit("expected 8 chunks")
    seen = {a: {} for a in ARMS}
    ncsv = 0
    for ch in rollout["chunks"]:
        plan_path = Path(ch["plan"])
        must_sha(plan_path, ch["sha256"], "plan")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan.get("code_manifest_sha256") != cfg["code_manifest_sha256"]:
            raise SystemExit("code manifest sha")
        if Path(plan["code"]).resolve() != code.resolve():
            raise SystemExit("code path/sha")
        if plan.get("mode") != "heldout" or plan.get("ensemble"):
            raise SystemExit("mode/ensemble")
        if set(plan_arm_names(plan)) != set(ARMS):
            raise SystemExit("plan arms")
        ok, run = released(ch["run"])
        if not ok:
            raise SystemExit("chunk not wrapper_exit0/supervision released")
        pm = plan_movies(plan)
        if int(ch.get("n_movies", len(pm))) != len(pm):
            raise SystemExit("n_movies")
        if len(pm) != len(set(pm)) or not set(pm).issubset(cmap):
            raise SystemExit("plan cohort identity")
        if plan["manifest_sha256"] != cfg["cohort_sha256"]:
            raise SystemExit("plan cohort hash")
        outd = Path(plan["output"])
        if outd.resolve() != (Path(ch["run"]) / "output").resolve():
            raise SystemExit("output path")
        expected_files = {"%s__%s.%s" % (a, ds, ext) for a in ARMS for ds in pm for ext in ("csv", "json")} | {"complete.json"}
        if {p.name for p in outd.iterdir()} != expected_files:
            raise SystemExit("extra/missing output artifacts")
        completed = json.loads((outd / "complete.json").read_text())
        if completed["status"] != "PASS_NO_LABEL_CHUNK" or completed["mode"] != "heldout":
            raise SystemExit("chunk completion")
        completion_records = {(r["contract"]["arm"], r["contract"]["dataset"]): r for r in completed["records"]}
        if len(completion_records) != 2 * len(pm) or len(completed["records"]) != 2 * len(pm):
            raise SystemExit("completion records")
        for arm in ARMS:
            for ds in pm:
                csvp = outd / ("%s__%s.csv" % (arm, ds))
                recp = outd / ("%s__%s.json" % (arm, ds))
                if not csvp.is_file() or not recp.is_file():
                    raise SystemExit("missing %s" % csvp)
                rec = json.loads(recp.read_text(encoding="utf-8"))
                c = rec["contract"]
                for k in CK:
                    if k not in c:
                        raise SystemExit("contract missing %s" % k)
                if c["arm"] != arm or c["dataset"] != ds or c["mode"] != "heldout" or c.get("ensemble"):
                    raise SystemExit("contract identity")
                if int(c["fold"]) != fold_of(ds) or int(c["fold"]) != int(cmap[ds]["fold"]):
                    raise SystemExit("fold leak %s" % ds)
                digest = sha(csvp)
                if digest != rec["csv_sha256"]:
                    raise SystemExit("csv sha %s" % csvp)
                if c["weight_sha256"] != weights[arm][fold_of(ds)]:
                    raise SystemExit("weight sha")
                if c["manifest_sha256"] != cfg["cohort_sha256"]:
                    raise SystemExit("manifest sha")
                if c["decoder_sha256"] != decoder:
                    raise SystemExit("decoder sha")
                if c["code_sha256"] != cfg["code_manifest_sha256"]:
                    raise SystemExit("code sha")
                if rec != completion_records.get((arm, ds)):
                    raise SystemExit("completion receipt mismatch")
                if rec["shape"] != cmap[ds]["shape"]:
                    raise SystemExit("receipt shape mismatch")
                graphs = analyze.read_graphs(csvp)
                if set(graphs) != {ds}:
                    raise SystemExit("csv datasets %s" % csvp)
                g = graphs[ds]
                shape = list(rec.get("shape") or cmap[ds]["shape"])
                for nid, pt in g["nodes"].items():
                    t, z, y, x = pt
                    if any(not np.isfinite(v) or float(v) != int(v) for v in pt):
                        raise SystemExit("noninteger/nonfinite coordinates")
                    if not (0 <= t < shape[0] and 0 <= z < shape[1] and 0 <= y < shape[2] and 0 <= x < shape[3]):
                        raise SystemExit("bounds %s %s" % (ds, nid))
                if ds in seen[arm]:
                    raise SystemExit("duplicate %s %s" % (arm, ds))
                seen[arm][ds] = {"csv": str(csvp), "sha256": digest, "zarr": cmap[ds].get("zarr")}
                ncsv += 1
                del graphs, g
    if ncsv != 350:
        raise SystemExit("expected 350 csvs, got %s" % ncsv)
    for arm in ARMS:
        extra, missing = set(seen[arm]) - set(cmap), set(cmap) - set(seen[arm])
        if extra or missing:
            raise SystemExit("%s extra/missing" % arm)
    return seen, cmap, run


def score_one(name, g, ds, estimate, evaluate, node_recall, per_sample_metrics, build_graph):
    ids = sorted(g["nodes"])
    indices = {n: i for i, n in enumerate(ids)}
    points = np.asarray([g["nodes"][n] for n in ids], dtype=float).reshape(-1, 4)
    edges = [(indices[s], indices[t], 1.0, 0.0) for s, t in g["edges"]]
    graph = build_graph(points, edges)
    metric = evaluate(graph, ds.tracks, scale=ds.scale)
    recall = node_recall(graph, ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
    return {"dataset": name, **per_sample_metrics(metric, float(estimate), recall)}


def classic_map(obj):
    rows = obj.get("rows", obj)
    if isinstance(rows, dict):
        rows = rows.get("classical") or rows.get("public") or rows
    if isinstance(rows, dict):
        return rows
    return {r["dataset"]: r for r in rows}


def by_embryo(rows, summarise):
    out = {}
    for e in ("44b6", "6bba"):
        sub = [r for r in rows if r["dataset"].startswith(e + "_")]
        out[e] = summarise(sub) if sub else {}
    return out


def write_mini_csv(path, name):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerow({"id": 0, "dataset": name, "row_type": "node", "node_id": 1, "t": 0, "z": 0, "y": 0, "x": 0,
                    "source_id": -1, "target_id": -1})
        w.writerow({"id": 1, "dataset": name, "row_type": "node", "node_id": 2, "t": 1, "z": 0, "y": 0, "x": 0,
                    "source_id": -1, "target_id": -1})
        w.writerow({"id": 2, "dataset": name, "row_type": "edge", "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1,
                    "source_id": 1, "target_id": 2})


def self_test():
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent.parent / "tests"), pattern="test_exp223_official_gate.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0:
        raise SystemExit("official gate regression tests failed or absent")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.config:
        raise SystemExit("--config required")
    t0 = time.time()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    evaluator_pins(cfg)
    must_sha(cfg["analyze_path"], cfg["analyze_sha256"], "analyze")
    analyze = load_mod(cfg["analyze_path"], "analyze_submission_edge_failure_modes")
    seen, cmap, _run = gate_all(cfg, analyze)
    gate = {"status": "PASS_ALL_PREDICTIONS_BEFORE_LABEL_ACCESS", "n_csv": 350, "arms": list(ARMS),
            "n_movies": 175, "heldout_map": {"44b6": 0, "6bba": 1}, "no_ensemble": True}
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "no_metric_gate.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    must_sha(cfg["baseline_metrics_path"], cfg["baseline_metrics_sha256"], "baseline")
    must_sha(cfg["classical_result_path"], cfg["classical_result_sha256"], "classical_result")
    sys.path[:0] = [str(Path(cfg["repo_path"]) / "src"), str(Path(cfg["repo_path"]) / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from geff import GeffMetadata
    from predict_unet_transformer import build_graph
    frozen = json.loads(Path(cfg["baseline_metrics_path"]).read_text(encoding="utf-8"))
    barm = cfg.get("baseline_arm", "public")
    base_graphs, _man = analyze.merge_verified_csv_graphs(frozen, barm)
    frozen_rows = {r["dataset"]: r for r in frozen["rows"][barm]}
    if set(frozen_rows) != set(cmap) or set(base_graphs) != set(cmap):
        raise SystemExit("baseline 175 ids")
    cres = classic_map(json.loads(Path(cfg["classical_result_path"]).read_text(encoding="utf-8")))
    if set(cres) != set(cmap):
        raise SystemExit("classical 175 ids")
    data = Path(cfg["data_path"])
    arm_rows = {a: [] for a in ARMS}
    base_rows, paired = [], []
    for name in sorted(cmap):
        zarr = cmap[name].get("zarr") or str(data / ("%s.zarr" % name))
        ds = open_dataset(zarr, require_tracks=True, load_image=False)
        geff = data / ("%s.geff" % name)
        estimate = (GeffMetadata.read(str(geff)).extra or {})["estimated_number_of_nodes"]
        brow = score_one(name, base_graphs[name], ds, estimate, evaluate, node_recall, per_sample_metrics, build_graph)
        rows_close(brow, frozen_rows[name])
        base_rows.append(brow)
        prow = {"dataset": name, "baseline": brow, "classical": cres[name]}
        for arm in ARMS:
            g = analyze.read_graphs(Path(seen[arm][name]["csv"]))[name]
            arow = score_one(name, g, ds, estimate, evaluate, node_recall, per_sample_metrics, build_graph)
            arm_rows[arm].append(arow)
            prow[arm] = arow
            del g
        paired.append(prow)
        print(json.dumps({"scored": name}), flush=True)
    result = {
        "status": "PASS_EXP223_OFFICIAL_BOTH_ARMS", "elapsed_seconds": time.time() - t0,
        "no_metric_gate_sha256": sha(out / "no_metric_gate.json"),
        "author_199_claim": "not_compared", "ensemble": False,
        "summary": {a: summarise(arm_rows[a]) for a in ARMS},
        "summary_by_embryo": {a: by_embryo(arm_rows[a], summarise) for a in ARMS},
        "baseline_summary": summarise(base_rows),
        "rows": arm_rows, "paired_rows": paired, "baseline_replay": "PASS_1e-12",
        "classical_result_sha256": cfg["classical_result_sha256"],
        "note": "comparable 175 official; not unbiased CV; n=2 development-adapted",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "summary": result["summary"]}), flush=True)


if __name__ == "__main__":
    main()
