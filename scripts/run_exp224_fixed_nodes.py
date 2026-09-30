#!/usr/bin/env python3
"""EXP224: source8 CONTROL13 final nodes; reference graph vs EXP002 link_frames.

Predictions+CSV/hash/graph gates before GT. No detection/refine/prune/gapclose.
No 6bba, no new DL, no embryo-router. development-adapted n=2 remains.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
MAX_LINK_UM = 8.0


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


def load_classical(path, expected):
    must_sha(path, expected, "classical")
    text = Path(path).read_text(encoding="utf-8")
    if text.count("import pandas as pd\n") != 1:
        raise SystemExit("classical pandas import contract failed")
    spec = importlib.util.spec_from_file_location("exp002_exact", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    exec(compile(text.replace("import pandas as pd\n", ""), str(path), "exec"), mod.__dict__)
    if not hasattr(mod, "link_frames"):
        raise SystemExit("classical missing link_frames")
    return mod


def to_frames(nodes, t_max):
    items = []
    for nid, (t, z, y, x) in nodes.items():
        t = int(t)
        if t < 0 or t >= int(t_max):
            raise SystemExit("t out of range %s" % t)
        items.append((t, float(z), float(y), float(x), int(nid)))
    items.sort()
    frames = [[] for _ in range(int(t_max))]
    old_to_new = {}
    new = 1
    for t, z, y, x, nid in items:
        frames[t].append((z, y, x))
        old_to_new[nid] = new
        new += 1
    arrays = [np.asarray(fr, dtype=np.float64).reshape(-1, 3) for fr in frames]
    return arrays, old_to_new


def remap_graph(nodes, edges, old_to_new):
    new_nodes = {}
    for nid, p in nodes.items():
        nn = old_to_new[int(nid)]
        new_nodes[nn] = (int(p[0]), float(p[1]), float(p[2]), float(p[3]))
    new_edges = []
    for s, tgt in edges:
        s, tgt = int(s), int(tgt)
        if s not in old_to_new or tgt not in old_to_new:
            raise SystemExit("edge references unknown node")
        new_edges.append((old_to_new[s], old_to_new[tgt]))
    return {"nodes": new_nodes, "edges": new_edges}


def tg_to_graph(g):
    nodes = {}
    for i, nid in enumerate(g.node_ids):
        nodes[int(nid)] = (int(g.node_t[i]), float(g.node_z[i]), float(g.node_y[i]), float(g.node_x[i]))
    if g.n_edges == 0:
        return {"nodes": nodes, "edges": []}
    return {"nodes": nodes, "edges": [(int(s), int(t)) for s, t in np.asarray(g.edges).reshape(-1, 2)]}


def graph_rows(name, g):
    rows = []
    for nid in sorted(g["nodes"], key=lambda k: (g["nodes"][k][0], k)):
        t, z, y, x = g["nodes"][nid]
        rows.append({"dataset": name, "row_type": "node", "node_id": int(nid), "t": int(t),
                     "z": z, "y": y, "x": x, "source_id": -1, "target_id": -1})
    for s, tgt in g["edges"]:
        rows.append({"dataset": name, "row_type": "edge", "node_id": -1, "t": -1, "z": -1, "y": -1,
                     "x": -1, "source_id": int(s), "target_id": int(tgt)})
    return rows


def write_csv(path, names, graphs):
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        i = 0
        for name in names:
            for row in graph_rows(name, graphs[name]):
                w.writerow({"id": i, **row})
                i += 1


def node_lock(names, graphs):
    h = hashlib.sha256()
    for name in names:
        for nid, (t, z, y, x) in sorted(graphs[name]["nodes"].items(), key=lambda kv: (kv[1][0], kv[0])):
            h.update(("%s:%s:%s:%.16g:%.16g:%.16g\n" % (name, nid, t, z, y, x)).encode())
    return h.hexdigest()


def rows_close(got, exp, tol=1e-12):
    for k, v in exp.items():
        if k not in got:
            raise SystemExit("missing field %s" % k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if abs(float(got[k]) - float(v)) > tol:
                raise SystemExit("control replay %s: %s != %s" % (k, got[k], v))
        elif got[k] != v:
            raise SystemExit("control replay %s mismatch" % k)


def resolve(cfg):
    cfg = dict(cfg)
    if cfg.get("package_path"):
        must_sha(cfg["package_path"], cfg["package_sha256"], "package")
        pkg = json.loads(Path(cfg["package_path"]).read_text(encoding="utf-8"))
        cfg.setdefault("repo_path", pkg["repo"])
        cfg.setdefault("data_path", pkg["data"])
        cfg.setdefault("control_csv", pkg["control_csv"])
        if not cfg.get("movies"):
            movies = []
            for ds, meta in pkg["datasets"].items():
                movies.append({
                    "dataset": ds, "shape": meta["shape_tzyx"], "scale": meta["voxel_scale_zyx_um"],
                    "estimated_number_of_nodes": meta["estimated_number_of_nodes"],
                    "zarr": meta.get("zarr"), "geff": meta.get("geff"),
                })
            cfg["movies"] = movies
        met = cfg.get("control_metrics") or pkg.get("source_graph_metrics")
        if isinstance(met, dict) and "path" in met:
            cfg["control_metrics"] = met
    return cfg


def self_test():
    nodes = {99: (2, 0.0, 0.0, 0.0), 7: (0, 0.0, 0.0, 0.0), 8: (0, 1.0, 0.0, 0.0)}
    frames, mapping = to_frames(nodes, 4)
    assert mapping == {7: 1, 8: 2, 99: 3}, mapping
    assert frames[1].shape == (0, 3) and frames[3].shape == (0, 3)
    assert frames[0].shape == (2, 3) and int(frames[0][0, 1]) == 0
    ref = remap_graph(nodes, [(7, 99)], mapping)
    assert ref["edges"] == [(1, 3)] and set(ref["nodes"]) == {1, 2, 3}
    scale = np.asarray([2.0, 0.5, 0.5], dtype=np.float64)
    dz = float(np.sqrt(((np.array([1.0, 0.0, 0.0]) * scale) ** 2).sum()))
    dxy = float(np.sqrt(((np.array([0.0, 0.0, 5.0]) * scale) ** 2).sum()))
    assert abs(dz - 2.0) <= 1e-12 and abs(dxy - 2.5) <= 1e-12
    inc, outd = {}, {}
    for s, t in ((1, 2), (1, 3)):
        inc[t] = inc.get(t, 0) + 1
        outd[s] = outd.get(s, 0) + 1
    assert max(inc.values()) > 1 or max(outd.values()) == 2
    try:
        from scipy.optimize import linear_sum_assignment
        r, c = linear_sum_assignment(np.array([[0.1, 9.0], [9.0, 0.2]]))
        assert list(zip([int(x) for x in r], [int(x) for x in c])) == [(0, 0), (1, 1)]
    except ImportError:
        pass
    print(json.dumps({"status": "PASS_SELF_TEST_EXP224"}))


def score_graphs(names, movies, graphs, data, repo):
    sys.path[:0] = [str(Path(repo) / "src"), str(Path(repo) / "scripts")]
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    mm = {m["dataset"]: m for m in movies}
    rows = []
    for name in names:
        zarr = mm[name].get("zarr") or str(Path(data) / ("%s.zarr" % name))
        ds = open_dataset(zarr, require_tracks=True, load_image=False)
        from geff import GeffMetadata
        assert np.allclose(ds.scale, mm[name]["scale"], rtol=0, atol=1e-12)
        estimate = float((GeffMetadata.read(Path(data)/(name+".geff")).extra or {})["estimated_number_of_nodes"])
        assert estimate == float(mm[name]["estimated_number_of_nodes"])
        g = graphs[name]
        ids = sorted(g["nodes"])
        indices = {n: i for i, n in enumerate(ids)}
        points = np.asarray([g["nodes"][n] for n in ids], dtype=float).reshape(-1, 4)
        edges = [(indices[s], indices[t], 1.0, 0.0) for s, t in g["edges"]]
        graph = build_graph(points, edges)
        metric = evaluate(graph, ds.tracks, scale=ds.scale)
        recall = node_recall(graph, ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
        rows.append({"dataset": name, **per_sample_metrics(metric, estimate, recall)})
    return rows, summarise(rows)


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
    cfg = resolve(json.loads(Path(args.config).read_text(encoding="utf-8")))
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=False)
    must_sha(cfg["analyze_path"], cfg["analyze_sha256"], "analyze")
    analyze = load_mod(cfg["analyze_path"], "analyze_submission_edge_failure_modes")
    if hasattr(analyze, "COLUMNS") and list(analyze.COLUMNS) != COLUMNS:
        raise SystemExit("COLUMNS mismatch")
    for pin in cfg["evaluator_pins"]:
        must_sha(pin["path"], pin["sha256"], "evaluator")
    csv_obj, met_obj = cfg["control_csv"], cfg["control_metrics"]
    must_sha(csv_obj["path"], csv_obj["sha256"], "control_csv")
    must_sha(met_obj["path"], met_obj["sha256"], "control_metrics")
    movies = cfg["movies"]
    names = [m["dataset"] for m in movies]
    if len(names) != 8 or len(set(names)) != 8 or set(names) != set(cfg["source_movies"]) or any(not n.startswith("44b6_") for n in names):
        raise SystemExit("EXP224 requires source-only 8 44b6 movies")
    control = analyze.read_graphs(Path(csv_obj["path"]))
    if set(control) != set(names):
        raise SystemExit("control movies mismatch")
    mod = load_classical(cfg["classical_path"], cfg["classical_sha256"])
    ref_g, phys_g, mmap = {}, {}, {m["dataset"]: m for m in movies}
    for name in names:
        shape, nodes, edges = mmap[name]["shape"], control[name]["nodes"], control[name]["edges"]
        if not nodes:
            raise SystemExit("%s empty nodes" % name)
        for nid, (t, z, y, x) in nodes.items():
            if not (0 <= int(t) < shape[0] and 0 <= z < shape[1] and 0 <= y < shape[2] and 0 <= x < shape[3]):
                raise SystemExit("%s node %s out of bounds" % (name, nid))
        frames, mapping = to_frames(nodes, int(shape[0]))
        if len(mapping) != len(nodes):
            raise SystemExit("node drop")
        ref_g[name] = {"nodes": dict(nodes), "edges": list(edges)}
        mod.SCALE = np.asarray(mmap[name]["scale"], dtype=np.float64)
        phys = tg_to_graph(mod.link_frames(frames, max_link_um=MAX_LINK_UM, allow_divisions=False))
        phys = remap_graph(phys["nodes"], phys["edges"], {new: old for old, new in mapping.items()})
        if phys["nodes"] != ref_g[name]["nodes"]:
            raise SystemExit("%s physical nodes != locked nodes" % name)
        inc, outd = {}, {}
        for a, b in phys["edges"]:
            assert nodes[b][0] == nodes[a][0] + 1
            inc[b] = inc.get(b, 0) + 1; outd[a] = outd.get(a, 0) + 1
        assert max(inc.values(), default=0) <= 1 and max(outd.values(), default=0) <= 1
        phys_g[name] = phys
        print(json.dumps({"dataset": name, "nodes": len(nodes), "ref_edges": len(ref_g[name]["edges"]),
                          "phys_edges": len(phys["edges"])}), flush=True)
    assert all(ref_g[n]["nodes"] == control[n]["nodes"] and ref_g[n]["edges"] == control[n]["edges"] for n in names)
    lock = node_lock(names, ref_g)
    if node_lock(names, phys_g) != lock:
        raise SystemExit("node lock sha mismatch between arms")
    write_csv(out / "reference.csv", names, ref_g)
    write_csv(out / "physical.csv", names, phys_g)
    ref_loaded = analyze.read_graphs(out / "reference.csv")
    phys_loaded = analyze.read_graphs(out / "physical.csv")
    if set(ref_loaded) != set(names) or set(phys_loaded) != set(names):
        raise SystemExit("csv movie gate failed")
    assert all(ref_loaded[n] == ref_g[n] and phys_loaded[n] == phys_g[n] for n in names)
    gate = {
        "status": "PASS_ALL_PREDICTIONS_BEFORE_LABEL_ACCESS", "movies": names,
        "reference_sha256": sha(out / "reference.csv"), "physical_sha256": sha(out / "physical.csv"),
        "node_lock_sha256": lock, "control_csv_sha256": csv_obj["sha256"],
        "classical_sha256": cfg["classical_sha256"], "package_sha256": cfg.get("package_sha256"),
        "max_link_um": MAX_LINK_UM, "allow_divisions": False,
    }
    (out / "no_metric_gate.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    ref_rows, ref_sum = score_graphs(names, movies, ref_loaded, cfg["data_path"], cfg["repo_path"])
    frozen = json.loads(Path(met_obj["path"]).read_text(encoding="utf-8"))
    crow = frozen.get("rows", {}).get("control")
    if crow is None:
        raise SystemExit("metrics json missing rows.control")
    cmap = {r["dataset"]: r for r in crow} if isinstance(crow, list) else crow
    rmap = {r["dataset"]: r for r in ref_rows}
    for name in names:
        rows_close(rmap[name], cmap[name])
    phys_rows, phys_sum = score_graphs(names, movies, phys_loaded, cfg["data_path"], cfg["repo_path"])
    pins = {
        "package_path": cfg.get("package_path"), "package_sha256": cfg.get("package_sha256"),
        "classical_path": cfg["classical_path"], "classical_sha256": cfg["classical_sha256"],
        "output_dir": str(out), "repo_path": cfg["repo_path"], "data_path": cfg["data_path"],
        "analyze_path": cfg["analyze_path"], "analyze_sha256": cfg["analyze_sha256"],
    }
    result = {
        "status": "PASS_EXP224_SOURCE8_FIXED_NODES", "elapsed_seconds": time.time() - t0,
        "provenance": gate, "no_metric_gate_sha256": sha(out / "no_metric_gate.json"),
        "node_lock_sha256": lock, "rows": {"reference": ref_rows, "physical": phys_rows},
        "summary": {"reference": ref_sum, "physical": phys_sum},
        "summary_by_embryo": {"44b6": {"reference": ref_sum, "physical": phys_sum}},
        "pins": pins, "note": "development-adapted; source8 only; no 6bba; no embryo-router",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "config_used.json").write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "summary": result["summary"], "node_lock_sha256": lock}), flush=True)


if __name__ == "__main__":
    main()
