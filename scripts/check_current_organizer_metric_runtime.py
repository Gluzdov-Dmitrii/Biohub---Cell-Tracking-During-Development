"""Reusable pinned organizer-metric runtime and synthetic API contract.

This module never opens competition labels. EXP234 and later EXP227 scorers can
share its isolated Python 3.11 environment and source/API checks.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import sys


ORGANIZER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
METRIC_SHA256 = {
    "metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
INIT_SHA256 = "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6"
PROFILES = {
    "remote_py311": {
        "python": (3, 11), "tracksdata": "0.1.0rc11", "polars": "1.44.1",
        "scipy": "1.17.1", "numpy": "2.4.6", "zarr": "3.1.6",
        "geff": "1.3.1.1.3", "bidict": "0.24.1", "blosc2": "4.12.0",
        "dask": "2026.8.0", "ilpy": "0.6.0", "imagecodecs": "2026.3.6",
        "numba": "0.67.0", "numcodecs": "0.15.1", "psygnal": "0.15.1",
        "pyarrow": "25.0.1", "rich": "15.0.0", "rstar-python": "0.2.0",
        "rustworkx": "0.18.1", "scikit-image": "0.26.0",
        "sqlalchemy": "2.0.52", "tqdm": "4.70.0",
        "typing-extensions": "4.16.0",
    },
    "local_contract_py312": {
        "python": (3, 12), "tracksdata": "0.1.0rc11", "polars": "1.44.2",
        "scipy": "1.18.1", "numpy": "2.5.3", "zarr": "3.4.0",
        "geff": "1.3.1.1.3",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_runtime(profile: str) -> dict:
    expected = PROFILES[profile]
    assert sys.version_info[:2] == expected["python"]
    versions = {name: metadata.version(name) for name in expected if name != "python"}
    assert versions == {name: version for name, version in expected.items() if name != "python"}
    direct = json.loads(metadata.distribution("tracksdata").read_text("direct_url.json"))
    assert direct["vcs_info"]["commit_id"] == TRACKSDATA_COMMIT
    assert direct["vcs_info"]["requested_revision"] == TRACKSDATA_COMMIT
    return {"profile": profile, "python": ".".join(map(str, expected["python"])),
            "versions": versions, "tracksdata_commit": TRACKSDATA_COMMIT}


def load_metric(package_root: Path):
    package_root = package_root.resolve()
    package = package_root / "tracking_cellmot_official"
    assert package.is_dir() and sha(package / "__init__.py") == INIT_SHA256
    for name, digest in METRIC_SHA256.items():
        assert sha(package / name) == digest, name
    sys.path.insert(0, str(package_root))
    metric = importlib.import_module("tracking_cellmot_official.metrics")
    division = importlib.import_module("tracking_cellmot_official.division_metrics")
    assert Path(metric.__file__).resolve() == package / "metrics.py"
    assert Path(division.__file__).resolve() == package / "division_metrics.py"
    return metric


def make_graph(nodes, edges):
    import polars as pl
    import tracksdata as td

    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, 0.0)
    ids = {}
    for key, (t, z, y, x) in nodes.items():
        ids[key] = graph.add_node({"t": t, "z": z, "y": y, "x": x})
    for source, target in edges:
        graph.add_edge(ids[source], ids[target], {})
    return graph


def synthetic_contract(metric) -> dict:
    gt_nodes = {"gp": (0, 0., 0., 0.), "p": (1, 0., 0., 0.),
                "a": (2, 0., 0., -1.), "b": (2, 0., 0., 1.),
                "aa": (3, 0., 0., -1.), "bb": (3, 0., 0., 1.)}
    gt_edges = [("gp", "p"), ("p", "a"), ("p", "b"),
                ("a", "aa"), ("b", "bb")]
    remote_fork_nodes = {"f": (0, 0., 0., 50.), "p": gt_nodes["p"],
                         "q": (1, 0., 0., 50.), "a": gt_nodes["a"],
                         "b": gt_nodes["b"], "aa": gt_nodes["aa"],
                         "bb": gt_nodes["bb"]}
    remote_fork_edges = [("f", "p"), ("f", "q"), ("p", "a"),
                         ("q", "b"), ("a", "aa"), ("b", "bb")]
    positive = metric.evaluate(make_graph(gt_nodes, gt_edges),
                               make_graph(gt_nodes, gt_edges), scale=(1., 1., 1.))
    negative = metric.evaluate(make_graph(remote_fork_nodes, remote_fork_edges),
                               make_graph(gt_nodes, gt_edges), scale=(1., 1., 1.))
    assert (positive.division_tp, positive.division_fn) == (1, 0)
    assert (negative.division_tp, negative.division_fn) == (0, 1)
    return {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT",
            "positive_division": [positive.division_tp, positive.division_fp,
                                  positive.division_fn],
            "remote_weak_component_division": [negative.division_tp,
                                                negative.division_fp,
                                                negative.division_fn]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    args = parser.parse_args()
    runtime = validate_runtime(args.profile)
    metric = load_metric(args.package_root)
    contract = synthetic_contract(metric)
    print(json.dumps({**runtime, **contract, "organizer_commit": ORGANIZER_COMMIT,
                      "metric_sha256": METRIC_SHA256}))


if __name__ == "__main__":
    main()
