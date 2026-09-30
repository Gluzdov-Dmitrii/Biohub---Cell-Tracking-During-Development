"""Local-only contracts for the EXP241 scorer handoff scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stage_exp241_source_paired_scorer import local_bundle, remote_preflight_source, remote_stage_source
from launch_exp241_source_paired_scorer import (
    command, cpu_wrapper_source, pinned_python_preflight_source, remote_launch_source,
    remote_readback_source,
)
from verify_exp241_source_paired_scorer import close_value, fixed_gate, remote_source


def test_exact_local_bundle_and_remote_templates_compile_without_ssh():
    manifest, config = local_bundle()
    assert len(manifest["files"]) == 12
    assert config["source_only"] and config["labels_read_at_prepare"] is False
    for source in (remote_preflight_source(False), remote_preflight_source(True),
                   remote_stage_source(manifest), pinned_python_preflight_source(),
                   cpu_wrapper_source(), remote_launch_source(manifest),
                   remote_readback_source(), remote_source("a" * 64, "b" * 64, "c" * 64)):
        compile(source, "remote_exp241", "exec")
        assert "@@" not in source
    assert command()[-2:] == ["--manifest-sha256",
                              "bd585c361c68b8b9e67bd1ebe0ba132a11c682dd5dec2116de6f78b36e714975"]


def test_wrapper_requires_cpu_and_hidden_cuda():
    wrapper = cpu_wrapper_source()
    assert "CUDA_VISIBLE_DEVICES=''" in wrapper
    assert "PYTHONOPTIMIZE='0'" in wrapper
    assert "RLIMIT_AS" in wrapper and "RLIMIT_CPU" in wrapper
    assert "start_new_session=True" in wrapper
    assert "exit.json" in wrapper


def make_summary(score, *, edge=0.8, division=0.5, recall=0.9, micro=0.9):
    return {"official": {"score": score, "adj_edge_jaccard": edge,
                         "division_jaccard": division, "node_recall": recall},
            "nodes": {"recall_micro": micro}}


def test_independent_verifier_recomputes_literal_fixed_gate():
    baseline = make_summary(0.8)
    assert fixed_gate(baseline, make_summary(0.805, edge=0.805))["pass"]
    assert not fixed_gate(baseline, make_summary(0.804999999, edge=0.805))["pass"]
    assert not fixed_gate(baseline, make_summary(0.81, edge=0.799))["pass"]
    assert not fixed_gate(baseline, make_summary(0.81, division=0.499))["pass"]
    assert not fixed_gate(baseline, make_summary(0.81, recall=0.899))["pass"]
    assert not fixed_gate(baseline, make_summary(0.81, micro=0.899))["pass"]


def test_independent_verifier_parent_replay_tolerance():
    close_value({"row": [1, 0.5 + 5e-13]}, {"row": [1, 0.5]}, "parent")
    close_value({"division_jaccard": None}, {"division_jaccard": float("nan")}, "pool")
    with pytest.raises(AssertionError):
        close_value({"row": [1, 0.5 + 2e-12]}, {"row": [1, 0.5]}, "parent")


def test_verifier_denies_geff_before_prior_or_result_access():
    source = remote_source("a" * 64, "b" * 64, "c" * 64)
    assert source.index("sys.addaudithook(deny)") < source.index("prior=json.loads")
    assert source.index("sys.addaudithook(deny)") < source.index("result=json.loads")
    assert "source_geff_reopened':False" in source
