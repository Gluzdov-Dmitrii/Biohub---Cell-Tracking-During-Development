"""Focused local checks for EXP239's one-shot completion verifier."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_exp239_division_fn_taxonomy as verify  # noqa: E402


def taxonomy_fixture():
    config = {"cohorts": []}
    gate = {
        "status": "PASS_EXP239_SOURCE19_GRAPH_METRIC_GATE_BEFORE_LABEL_ACCESS",
        "bundle_sha256": verify.MANIFEST_SHA,
        "reciprocal_target_labels_read": False,
        "runtime": {"profile": "remote_py311", "tracksdata_commit": verify.TRACKSDATA_COMMIT},
        "synthetic_contract": {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"},
        "cohorts": [],
    }
    result = {
        "status": "PASS_EXP239_SOURCE19_DIVISION_FN_TAXONOMY",
        "organizer_commit": verify.ORGANIZER_COMMIT,
        "metric_shas": verify.METRIC_SHAS,
        "source_division_events": 14,
        "source_division_fns": 11,
        "reciprocal_target_labels_read": False,
        "gpu_used": False,
        "kaggle_post": False,
        "cohorts": [],
    }
    prior = {"cohorts": []}
    for index, (experiment, size, categories, counts) in enumerate((
        ("EXP227", 8, ["recovered"] * 2 + ["no_local_fork"] * 3,
         {"tp": 2, "fp": 6, "fn": 3}),
        ("EXP236", 11, ["recovered"] + ["fewer_than_two_daughter_lineages"] * 2
         + ["no_local_fork"] * 6, {"tp": 1, "fp": 9, "fn": 8}),
    )):
        names = [f"source{index}_{i}" for i in range(size)]
        graph_hashes = [{"dataset": name, "csv_sha256": "a" * 64} for name in names]
        labels = [{"dataset": name, "tree_sha256": "b" * 64,
                   "files": 2, "previously_pinned": False} for name in names]
        events = []
        for event_id, category in enumerate(categories):
            events.append({
                "dataset": names[0], "gt_divider_id": event_id,
                "category": category, "subtype": None,
                "matched_parent_side_nodes": 1,
                "represented_daughter_lineages":
                    1 if category == "fewer_than_two_daughter_lineages" else 2,
                "local_forks": 1 if category == "recovered" else 0,
                "directed_forks": 1 if category == "recovered" else 0,
                "valid_forks": 1 if category == "recovered" else 0,
            })
        movies = []
        for movie_index, name in enumerate(names):
            movie_events = events if movie_index == 0 else []
            movie_counts = counts if movie_index == 0 else {"tp": 0, "fp": 0, "fn": 0}
            movie_categories = {key: sum(e["category"] == key for e in movie_events)
                                for key in ("recovered", *verify.STAGES)}
            movies.append({"dataset": name, "counts": movie_counts,
                           "events": movie_events, "category_counts": movie_categories})
        source = {"experiment": experiment, "ids": names,
                  "graph_hashes": graph_hashes, "score_gate_sha256": "c" * 64,
                  "geff_tree_hashes": {}, "expected_division_counts": counts}
        config["cohorts"].append(source)
        gate["cohorts"].append({"experiment": experiment, "ids": names,
                                "graph_hashes": copy.deepcopy(graph_hashes),
                                "prior_no_metric_gate_sha256": "c" * 64})
        result["cohorts"].append({"experiment": experiment, "movies": movies,
                                  "counts": counts, "category_counts": verify.EXPECTED_CATEGORIES[index],
                                  "label_hashes": labels})
        prior["cohorts"].append({"experiment": experiment, "label_hashes": [
            {"dataset": row["dataset"], "tree_sha256": row["tree_sha256"],
             "files": row["files"]} for row in labels]})
    return config, gate, result, prior


def test_exact_local_lineage_and_dry_run_avoid_remote_and_receipt(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(verify, "OUT", tmp_path / "absent_verification_receipt.json")
    manifest, stage, launch = verify.local_gate()
    assert len(manifest["files"]) == 8
    assert stage["manifest_sha256"] == launch["source_manifest_sha256"] == verify.MANIFEST_SHA
    assert not verify.OUT.exists()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("dry run attempted remote access")

    monkeypatch.setattr(verify, "ssh", forbidden)
    monkeypatch.setattr(sys, "argv", ["verify", "--dry-run"])
    verify.main()
    assert json.loads(capsys.readouterr().out)["receipt_write"] is False
    assert not verify.OUT.exists()


def test_generated_remote_readback_is_read_only_and_parses():
    source = verify.remote_check_source()
    tree = ast.parse(source)
    assert "if not __debug__:raise RuntimeError('EXP239 readback requires active assertions')" in source
    assert "sys.addaudithook(deny_geff)" in source
    assert "assert observed=={**manifest['files']" in source
    assert "launch_path.stat().st_mtime_ns < gate_path.stat().st_mtime_ns" in source
    assert "assert wrapper_state in (None,'Z')" in source
    assert "prior_path=root/'runs/source_inner_error_decomposition_v2_20260927/output/result.json'" in source
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and node.func.attr in {"write_text", "write_bytes", "mkdir", "unlink", "open"}
                   for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"open", "subprocess", "Popen"}
                   for node in ast.walk(tree))


def test_optimized_python_cannot_disable_verification_assertions():
    process = subprocess.run(
        [sys.executable, "-O", "-B", "-c",
         "import sys;sys.path.insert(0,'scripts');import verify_exp239_division_fn_taxonomy"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert process.returncode != 0
    assert "EXP239 verifier requires active assertions" in process.stderr


def test_taxonomy_accepts_exact_14_event_partition():
    summary = verify.verify_taxonomy(*taxonomy_fixture())
    assert summary["source_division_events"] == 14
    assert summary["source_division_fns"] == 11
    assert [row["counts"] for row in summary["summaries"]] == [
        {"tp": 2, "fp": 6, "fn": 3}, {"tp": 1, "fp": 9, "fn": 8}]
    assert [row["category_counts"]["no_local_fork"] for row in summary["summaries"]] == [3, 6]


@pytest.mark.parametrize("tamper", ["tree", "graph", "partition", "metric", "target"])
def test_taxonomy_rejects_tampered_lineage_or_partition(tamper):
    config, gate, result, prior = copy.deepcopy(taxonomy_fixture())
    if tamper == "tree":
        result["cohorts"][1]["label_hashes"][0]["tree_sha256"] = "f" * 64
    elif tamper == "graph":
        gate["cohorts"][0]["graph_hashes"][0]["csv_sha256"] = "d" * 64
    elif tamper == "partition":
        result["cohorts"][0]["movies"][0]["events"][2]["category"] = "directed_branch_failure"
    elif tamper == "metric":
        result["metric_shas"] = {}
    else:
        result["reciprocal_target_labels_read"] = True
    with pytest.raises(AssertionError):
        verify.verify_taxonomy(config, gate, result, prior)


def test_existing_receipt_blocks_even_local_preflight(monkeypatch, tmp_path):
    existing = tmp_path / "existing.json"
    existing.write_text("{}")
    monkeypatch.setattr(verify, "OUT", existing)
    with pytest.raises(AssertionError, match="receipt exists"):
        verify.local_gate()
