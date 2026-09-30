# test_exp229_fixed_nodes.py
"""Synthetic tests for run_exp229_fixed_nodes.py. No Kaggle data, no remote paths.

Code supplied; runtime checks pending. A fake helper + fake classical module are
written to a temp directory and implement only the contracts the producer uses.
The real-classical test is skipped unless the parent sets EXP229_REAL_HELPER and
EXP229_REAL_CLASSICAL; the parent must run that one explicitly.
"""
import csv
import hashlib
import importlib.util
import itertools
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if not (HERE / "run_exp229_fixed_nodes.py").exists():
    HERE = HERE.parent / "scripts"

FAKE_HELPER_SOURCE = r'''
"""Synthetic stand-in for the SHA-verified EXP224 helper (test-only)."""
import hashlib
import importlib.util
import json

def load_classical(path, expected_hash):
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    if digest != str(expected_hash).strip().lower():
        raise ValueError("fake helper: classical sha mismatch")
    spec = importlib.util.spec_from_file_location("exp229_fake_classical", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def to_frames(nodes, T):
    rows = sorted((int(t), float(z), float(y), float(x), int(node_id))
                  for node_id, (t, z, y, x) in nodes.items())
    frames = [[] for _ in range(int(T))]
    old_to_new = {}
    for new_id, (t, z, y, x, node_id) in enumerate(rows, start=1):
        frames[t].append((z, y, x))
        old_to_new[int(node_id)] = new_id
    return frames, old_to_new

def tg_to_graph(classical_graph):
    return {"nodes": {int(k): (int(v[0]), float(v[1]), float(v[2]), float(v[3]))
                      for k, v in classical_graph["nodes"].items()},
            "edges": [(int(a), int(b)) for a, b in classical_graph["edges"]]}

def remap_graph(nodes, edges, mapping):
    return {"nodes": {int(mapping[int(k)]): v for k, v in nodes.items()},
            "edges": [(int(mapping[int(a)]), int(mapping[int(b)])) for a, b in edges]}

def node_lock(names, graphs):
    payload = []
    for name in sorted(names):
        nodes = graphs[name]["nodes"]
        payload.append([name, sorted([int(k), int(v[0]), repr(float(v[1])),
                                      repr(float(v[2])), repr(float(v[3]))]
                                     for k, v in nodes.items())])
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

def write_csv(path, names, graphs):
    import csv as _csv
    columns = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
               "source_id", "target_id"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = _csv.writer(handle)
        writer.writerow(columns)
        row_id = 0
        for name in names:
            graph = graphs[name]
            for node_id, (t, z, y, x) in graph["nodes"].items():
                writer.writerow([row_id, name, "node", int(node_id), int(t),
                                 float(z), float(y), float(x), -1, -1])
                row_id += 1
            for source, target in graph["edges"]:
                writer.writerow([row_id, name, "edge", -1, -1, -1, -1, -1,
                                 int(source), int(target)])
                row_id += 1
'''

FAKE_CLASSICAL_SOURCE = r'''
"""Synthetic stand-in for the EXP002 physical linker (test-only)."""
import json
import os

SCALE = [1.0, 1.0, 1.0]

def _trace(entry):
    path = os.environ.get("EXP229_FAKE_TRACE")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

def link_frames(frames, max_link_um=8.0, allow_divisions=False):
    scale = [float(v) for v in SCALE]
    _trace({"scale": scale, "max_link_um": float(max_link_um),
            "allow_divisions": bool(allow_divisions), "frames": len(frames)})
    if allow_divisions:
        raise AssertionError("EXP229 must pass allow_divisions=False")
    nodes, edges = {}, []
    index = []
    new_id = 0
    for t, frame in enumerate(frames):
        current = []
        for z, y, x in frame:
            new_id += 1
            nodes[new_id] = (t, float(z), float(y), float(x))
            current.append(new_id)
        index.append(current)
    used_sources = set()
    for t in range(len(frames) - 1):
        used_targets = set()
        for source in index[t]:
            if source in used_sources:
                continue
            _, sz, sy, sx = nodes[source]
            best = None
            for target in index[t + 1]:
                if target in used_targets:
                    continue
                _, tz, ty, tx = nodes[target]
                distance = sum(((b - a) * s) ** 2
                               for a, b, s in zip((sz, sy, sx), (tz, ty, tx), scale)) ** 0.5
                if distance <= max_link_um and (best is None or distance < best[0]):
                    best = (distance, target)
            if best is not None:
                edges.append((source, best[1]))
                used_sources.add(source)
                used_targets.add(best[1])
    return {"nodes": nodes, "edges": edges}


def remap_renamer(nodes, edges, mapping):
    result = remap_graph(nodes, edges, mapping)
    renamed = {}
    for index, (key, value) in enumerate(result["nodes"].items()):
        renamed[key + 100000 if index == 0 else key] = value
    result["nodes"] = renamed
    return result


def remap_graph(nodes, edges, mapping):
    return {"nodes": {int(mapping[int(k)]): v for k, v in nodes.items()},
            "edges": [(int(mapping[int(a)]), int(mapping[int(b)])) for a, b in edges]}
'''

_counter = itertools.count()

def load_module_from(path, name):
    unique = "%s_%d" % (name, next(_counter))
    spec = importlib.util.spec_from_file_location(unique, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_runner():
    spec = importlib.util.spec_from_file_location("exp229_runner", HERE / "run_exp229_fixed_nodes.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["exp229_runner"] = module
    spec.loader.exec_module(module)
    return module

runner = load_runner()

def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_fake_modules(directory):
    helper_path = Path(directory) / "fake_helper.py"
    classical_path = Path(directory) / "fake_classical.py"
    helper_path.write_text(FAKE_HELPER_SOURCE, encoding="utf-8")
    classical_path.write_text(FAKE_CLASSICAL_SOURCE, encoding="utf-8")
    return helper_path, classical_path

def write_reference_csv(path, dataset, nodes, edges):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(runner.COLUMNS)
        ordered = sorted(nodes.items())
        for row_id, (node_id, (t, z, y, x)) in enumerate(ordered):
            writer.writerow([row_id, dataset, "node", int(node_id), int(t),
                             float(z), float(y), float(x), -1, -1])
        for offset, (source, target) in enumerate(edges, start=len(ordered)):
            writer.writerow([offset, dataset, "edge", -1, -1, -1, -1, -1,
                             int(source), int(target)])

def write_receipt(path, dataset, fold, csv_sha256):
    Path(path).write_text(json.dumps({
        "csv_sha256": csv_sha256,
        "contract": {"dataset": dataset, "arm": "selected50_20",
                     "fold": fold, "mode": "heldout"}}), encoding="utf-8")

def write_raw_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(runner.COLUMNS)
        writer.writerows(rows)

def read_trace(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]

class Exp229Tests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="exp229_test_")
        self.addCleanup(self.tempdir.cleanup)
        self.base = Path(self.tempdir.name)
        self.helper_path, self.classical_path = write_fake_modules(self.base)
        self.trace = self.base / "trace.jsonl"
        os.environ["EXP229_FAKE_TRACE"] = str(self.trace)
        self.addCleanup(os.environ.pop, "EXP229_FAKE_TRACE", None)

    def fake_modules(self):
        return (load_module_from(self.helper_path, "fake_helper"),
                load_module_from(self.classical_path, "fake_classical"))

    # --- transform: noncontiguous IDs, fractional coords, scale, anisotropy, cutoff ---
    def test_remap_preserves_ids_floats_and_applies_scale_anisotropy(self):
        helper, classical = self.fake_modules()
        self.assertEqual(tuple(float(v) for v in classical.SCALE), (1.0, 1.0, 1.0))
        nodes = {7: (0, 1.0, 2.0, 2.0),
                 40: (0, 1.0, 2.0, 6.0),
                 2: (1, 3.0, 2.0, 2.0),
                 88: (1, 1.5, 17.0, 2.25),
                 55: (1, 1.0, 24.0, 2.0),
                 99: (1, 1.0, 2.0, 30.0)}
        graph = {"nodes": nodes, "edges": [(40, 2)]}
        candidate = runner.transform_graph(graph, [2, 8, 32, 32], classical, helper)
        # scale is applied in place and observed by link_frames
        self.assertEqual(tuple(float(v) for v in classical.SCALE), runner.SCALE_ZYX_UM)
        calls = read_trace(self.trace)
        self.assertEqual(calls[-1]["scale"], [1.625, 0.40625, 0.40625])
        self.assertEqual(calls[-1]["max_link_um"], 8.0)
        self.assertFalse(calls[-1]["allow_divisions"])
        self.assertEqual(calls[-1]["frames"], 2)
        # node IDs and exact coordinates survive the sequential-ID round trip
        self.assertEqual(candidate["nodes"], nodes)
        self.assertEqual(set(candidate["nodes"]), {2, 7, 40, 55, 88, 99})
        # 7->2 at 3.25um; 40->88 at ~6.3um only because y uses 0.40625 um/voxel;
        # 55 at 8.9375um and 99 at 11.375um are past the 8um cutoff.
        self.assertEqual(set(candidate["edges"]), {(7, 2), (40, 88)})

    def test_missing_frames_and_isolated_nodes_preserved(self):
        helper, classical = self.fake_modules()
        nodes = {11: (0, 1.0, 1.0, 1.0), 12: (0, 2.0, 5.0, 5.0), 13: (3, 1.0, 1.5, 1.0)}
        candidate = runner.transform_graph({"nodes": nodes, "edges": []}, [4, 16, 32, 32],
                                           classical, helper)
        self.assertEqual(candidate["nodes"], nodes)
        self.assertEqual(candidate["edges"], [])
        self.assertEqual(read_trace(self.trace)[-1]["frames"], 4)

    def test_transform_rejects_node_changes(self):
        helper, _classical = self.fake_modules()
        original = helper.remap_graph
        def broken_remap(nodes, edges, mapping):
            graph = original(nodes, edges, mapping)
            first = next(iter(graph["nodes"]))
            t,z,y,x = graph["nodes"][first]
            graph["nodes"][first] = (t,z+0.25,y,x)
            return graph
        helper.remap_graph = broken_remap
        with self.assertRaises(runner.Exp229Error):
            runner.transform_graph({"nodes": {5: (0, 1.0, 1.0, 1.0)}, "edges": []},
                                   [2, 8, 32, 32], _classical, helper)

    # --- CSV malformed input ---
    def test_parse_csv_rejects_malformed_input(self):
        shape = [2, 8, 8, 8]
        dataset = "44b6_unit"
        good_node = [0, dataset, "node", 10, 0, 1.0, 2.0, 3.0, -1, -1]
        good_edge = [2, dataset, "edge", -1, -1, -1, -1, -1, 10, 11]
        candidates = {
            "fractional_t": [0, dataset, "node", 10, "0.5", 1.0, 2.0, 3.0, -1, -1],
            "out_of_bounds": [0, dataset, "node", 10, 0, 1.0, 2.0, 8.5, -1, -1],
            "negative_z": [0, dataset, "node", 10, 0, -1.0, 2.0, 3.0, -1, -1],
            "non_canonical_id": [0, dataset, "node", "007", 0, 1.0, 2.0, 3.0, -1, -1],
            "wrong_dataset": [0, "6bba_unit", "node", 10, 0, 1.0, 2.0, 3.0, -1, -1],
            "edge_with_node_id": [1, dataset, "edge", 10, -1, -1, -1, -1, 10, 11],
            "one_sided_edge": [1, dataset, "edge", -1, -1, -1, -1, -1, 10, -1],
        }
        for name, row in candidates.items():
            path = self.base / ("bad_%s.csv" % name)
            write_raw_csv(path, [row])
            with self.assertRaises(runner.Exp229Error, msg=name):
                runner.parse_csv(path, dataset, shape)
        duplicate = self.base / "duplicate_nodes.csv"
        write_raw_csv(duplicate, [good_node, [1, dataset, "node", 10, 0, 1.0, 2.0, 3.0, -1, -1]])
        with self.assertRaises(runner.Exp229Error):
            runner.parse_csv(duplicate, dataset, shape)
        duplicate_edge = self.base / "duplicate_edge.csv"
        write_raw_csv(duplicate_edge, [good_node,
                                       [1, dataset, "node", 11, 1, 1.0, 2.0, 3.0, -1, -1],
                                       good_edge, [3, dataset, "edge", -1, -1, -1, -1, -1, 10, 11]])
        with self.assertRaises(runner.Exp229Error):
            runner.parse_csv(duplicate_edge, dataset, shape)
        wrong_header = self.base / "wrong_header.csv"
        with open(wrong_header, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "dataset"])
            writer.writerow([0, dataset])
        with self.assertRaises(runner.Exp229Error):
            runner.parse_csv(wrong_header, dataset, shape)
        valid = self.base / "valid.csv"
        write_raw_csv(valid, [good_node, [1, dataset, "node", 11, 1, 1.0, 2.0, 3.0, -1, -1], good_edge])
        graph = runner.parse_csv(valid, dataset, shape)
        self.assertEqual(graph["nodes"], {10: (0, 1.0, 2.0, 3.0), 11: (1, 1.0, 2.0, 3.0)})
        self.assertEqual(graph["edges"], [(10, 11)])

    def test_validate_graph_rejects_edge_and_degree_violations(self):
        shape = [4, 8, 8, 8]
        nodes = {1: (0, 1.0, 1.0, 1.0), 2: (1, 1.0, 1.0, 1.0), 3: (2, 1.0, 1.0, 1.0),
                 4: (1, 2.0, 2.0, 2.0), 5: (1, 3.0, 3.0, 3.0)}
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": nodes, "edges": [(1, 3)]}, shape)  # non-consecutive
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": nodes, "edges": [(1, 99)]}, shape)  # missing endpoint
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": nodes, "edges": [(1, 2), (1, 2)]}, shape)  # duplicate
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": nodes, "edges": [(2, 4), (3, 4)]}, shape)  # indegree>1
        fan = {1: (0, 1, 1, 1), 2: (1, 1, 1, 1), 3: (1, 2, 2, 2), 4: (1, 3, 3, 3)}
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": fan, "edges": [(1, 2), (1, 3), (1, 4)]}, shape)
        with self.assertRaises(runner.Exp229Error):
            runner.validate_graph({"nodes": fan, "edges": [(1, 2), (1, 3)]}, shape, candidate=True)
        result = runner.validate_graph({"nodes": {50: (0, 1.0, 1.0, 1.0)},
                                        "edges": []}, shape)
        self.assertEqual(result["counts"]["isolated"], 1)
        self.assertEqual(result["counts"]["nodes"], 1)

    # --- SHA gates ---
    def test_sha_gates_reject_tampered_files(self):
        path = self.base / "tamper.bin"
        path.write_bytes(b"payload")
        digest = sha256_of(path)
        path.write_bytes(b"payload!")
        with self.assertRaises(runner.Exp229Error):
            runner.verify_sha256(path, digest)
        with self.assertRaises(runner.Exp229Error):
            runner.load_helper(self.helper_path, "0" * 64)
        config = self.base / "config.txt"
        config.write_text("experiment = 'EXP229'\n", encoding="utf-8")
        with self.assertRaises(runner.Exp229Error):
            runner.parse_config(config, "0" * 64)
        self.assertEqual(runner.parse_config(config, sha256_of(config))["experiment"], "EXP229")

    def test_receipt_contract_enforced(self):
        dataset, fold = "6bba_unit", 1
        reference = self.base / "receipt_reference.csv"
        write_reference_csv(reference, dataset, {1: (0, 1.0, 1.0, 1.0)}, [])
        receipt_path = self.base / "receipt.json"
        write_receipt(receipt_path, dataset, fold, sha256_of(reference))
        runner.verify_receipt(receipt_path, dataset, fold, sha256_of(reference))
        original = json.loads(receipt_path.read_text(encoding="utf-8"))
        for field, value in (("arm", "all"), ("mode", "train"), ("fold", 0), ("dataset", "44b6_unit")):
            broken = json.loads(json.dumps(original))
            broken["contract"][field] = value
            receipt_path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(runner.Exp229Error, msg=field):
                runner.verify_receipt(receipt_path, dataset, fold, sha256_of(reference))
        broken = json.loads(json.dumps(original))
        broken["csv_sha256"] = "e" * 64
        receipt_path.write_text(json.dumps(broken), encoding="utf-8")
        with self.assertRaises(runner.Exp229Error):
            runner.verify_receipt(receipt_path, "6bba_unit", 1, sha256_of(reference))

    def test_config_validation_rejects_bad_configs(self):
        row = {"dataset": "44b6_a", "shape": [2, 8, 8, 8], "reference_csv": "a.csv",
               "reference_sha256": "a" * 64, "receipt_path": "a.json", "receipt_sha256": "b" * 64}
        good = {"experiment": "EXP229", "output_dir": "out", "classical_path": "c.py",
                "classical_sha256": "c" * 64, "helper_path": "h.py", "helper_sha256": "d" * 64,
                "scale_zyx_um": [1.625, 0.40625, 0.40625], "rows": [row]}
        with self.assertRaises(runner.ConfigError):
            runner.validate_config(good)  # needs exactly 175 rows
        with self.assertRaises(runner.ConfigError):
            runner.validate_config(dict(good, experiment="EXP228"))
        with self.assertRaises(runner.ConfigError):
            runner.validate_config(dict(good, scale_zyx_um=[1.0, 1.0, 1.0]))
        with self.assertRaises(runner.ConfigError):
            runner.validate_config(dict(good, helper_sha256="nothex"))

    # --- end-to-end cohort on synthetic movies ---
    def _build_cohort(self):
        rows, expected = [], {}
        datasets = ([("44b6_%03d" % index, 0) for index in range(59)] +
                    [("6bba_%03d" % index, 1) for index in range(116)])
        for index, (dataset, fold) in enumerate(datasets):
            base_id = 1000 * (index + 1)
            nodes = {base_id + 3: (0, 1.0, 2.0, 2.0),
                     base_id + 40: (0, 1.0, 2.0, 6.0),
                     base_id + 2: (1, 2.0, 2.0, 2.0)}
            reference = self.base / ("%s_reference.csv" % dataset)
            write_reference_csv(reference, dataset, nodes, [(base_id + 40, base_id + 2)])
            receipt = self.base / ("%s_receipt.json" % dataset)
            write_receipt(receipt, dataset, fold, sha256_of(reference))
            rows.append({"dataset": dataset, "shape": [2, 8, 32, 32],
                         "reference_csv": str(reference), "reference_sha256": sha256_of(reference),
                         "receipt_path": str(receipt), "receipt_sha256": sha256_of(receipt)})
            expected[dataset] = {"nodes": nodes, "edges": [(base_id + 3, base_id + 2)]}
        output_dir = self.base / "outputs"
        config_path = self.base / "cohort_config.txt"
        lines = [
            "experiment = 'EXP229'",
            "output_dir = '%s'" % output_dir,
            "classical_path = '%s'" % self.classical_path,
            "classical_sha256 = '%s'" % sha256_of(self.classical_path),
            "helper_path = '%s'" % self.helper_path,
            "helper_sha256 = '%s'" % sha256_of(self.helper_path),
            "scale_zyx_um = [1.625, .40625, .40625]",
            "rows = [%s]" % ", ".join(
                "{dataset = '%s', shape = [2, 8, 32, 32], reference_csv = '%s', "
                "reference_sha256 = '%s', receipt_path = '%s', receipt_sha256 = '%s'}" % (
                    row["dataset"], row["reference_csv"], row["reference_sha256"],
                    row["receipt_path"], row["receipt_sha256"]) for row in rows),
        ]
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return config_path, output_dir, expected

    def test_end_to_end_cohort_streaming_and_complete_receipt(self):
        config_path, output_dir, expected = self._build_cohort()
        self.assertFalse(output_dir.exists())
        self.assertEqual(runner.run(config_path, sha256_of(config_path)), 0)
        complete = json.loads((output_dir / "complete.json").read_text(encoding="utf-8"))
        self.assertEqual(complete["status"], runner.COMPLETE_STATUS)
        self.assertEqual(complete["completed"], 175)
        self.assertEqual(len(complete["records"]), 175)
        self.assertEqual(complete["provenance"]["helper_sha256"], sha256_of(self.helper_path))
        self.assertEqual(complete["provenance"]["config_sha256"], sha256_of(config_path))
        self.assertEqual(json.loads((output_dir / "progress.json").read_text())["status"], "COMPLETE")
        self.assertEqual(len(list((output_dir / "receipts").glob("*.json"))), 175)
        calls = read_trace(self.trace)
        self.assertEqual(len(calls), 175)
        self.assertTrue(all(call["scale"] == [1.625, 0.40625, 0.40625] for call in calls))
        self.assertTrue(all(call["allow_divisions"] is False for call in calls))
        dataset = "6bba_000"
        output_csv = output_dir / ("physical__%s.csv" % dataset)
        self.assertTrue(output_csv.exists())
        reloaded = runner.validate_graph(runner.parse_csv(output_csv, dataset, [2, 8, 32, 32]),
                                         [2, 8, 32, 32], candidate=True)
        self.assertEqual(reloaded["nodes"], expected[dataset]["nodes"])
        self.assertEqual(reloaded["edges"], expected[dataset]["edges"])
        self.assertEqual(reloaded["counts"]["edges"], 1)
        self.assertEqual(reloaded["counts"]["isolated"], 1)

    def test_run_refuses_existing_output_dir(self):
        config_path, output_dir, _expected = self._build_cohort()
        output_dir.mkdir(parents=True)
        with self.assertRaises(runner.Exp229Error):
            runner.run(config_path, sha256_of(config_path))

    def test_invalid_config_never_creates_output_dir(self):
        output_dir = self.base / "never_created"
        config_path = self.base / "invalid_config.txt"
        config_path.write_text("experiment = 'EXP228'\noutput_dir = '%s'\n" % output_dir,
                               encoding="utf-8")
        with self.assertRaises(runner.ConfigError):
            runner.run(config_path, sha256_of(config_path))
        self.assertFalse(output_dir.exists())

    # --- worker guards ---
    def test_geff_audit_guard_blocks_and_cannot_be_disabled(self):
        with self.assertRaises(PermissionError):
            open(self.base / "movie.geff", "w", encoding="utf-8")
        with self.assertRaises(PermissionError):
            (self.base / "nested" / "movie.GEFF").mkdir(parents=True)
        with self.assertRaises(PermissionError):
            runner.sha256_file(self.base / "other.geff")
        self.assertFalse(hasattr(runner, "uninstall_audit_guard"))
        runner.install_audit_guard()  # idempotent

    def test_json_config_and_fractional_upper_voxel(self):
        config = self.base / "config.json"
        config.write_text(json.dumps({"experiment": "EXP229"}))
        self.assertEqual(runner.parse_config(config, sha256_of(config))["experiment"], "EXP229")
        graph = {"nodes": {4: (0, 7.75, 7.75, 7.75)}, "edges": []}
        self.assertEqual(runner.validate_graph(graph, [1,8,8,8])["nodes"], graph["nodes"])
        for x in [-1e-12, 8]:
            with self.assertRaises(runner.Exp229Error):
                runner.validate_graph({"nodes": {4:(0,0,0,x)},"edges":[]}, [1,8,8,8])

@unittest.skipUnless(os.environ.get("EXP229_REAL_HELPER") and os.environ.get("EXP229_REAL_CLASSICAL"),
                     "parent-only: set EXP229_REAL_HELPER and EXP229_REAL_CLASSICAL to run "
                     "the real reviewed helper/classical pins test")
class RealHelperPinsTest(unittest.TestCase):
    def test_real_helper_loads_and_official_scale_is_applied(self):
        helper_path = Path(os.environ["EXP229_REAL_HELPER"])
        classical_path = Path(os.environ["EXP229_REAL_CLASSICAL"])
        self.assertTrue(helper_path.is_file())
        self.assertTrue(classical_path.is_file())
        helper = runner.load_helper(helper_path, sha256_of(helper_path))
        classical = runner.load_classical_module(helper, classical_path, sha256_of(classical_path))
        self.assertTrue(runner.check_classical_pins(classical))
        observed = runner.apply_classical_scale(classical, runner.SCALE_ZYX_UM)
        self.assertEqual(observed, runner.SCALE_ZYX_UM)
        # Real implementation: anisotropic cutoff, empty frames, arbitrary IDs,
        # and fractional coordinates survive exactly.
        for delta, expected_edges in [((4,0,0), [(17,99)]), ((5,0,0), []), ((0,0,19), [(17,99)])]:
            graph = {"nodes": {17:(0,0.25,0.5,0.75),99:(1,0.25+delta[0],0.5+delta[1],0.75+delta[2]),7:(3,1.25,1.5,1.75)},"edges":[]}
            result = runner.transform_graph(graph,[5,64,64,64],classical,helper)
            self.assertEqual(result["nodes"],graph["nodes"])
            self.assertEqual(result["edges"],expected_edges)


if __name__ == "__main__":
    unittest.main(verbosity=2)
