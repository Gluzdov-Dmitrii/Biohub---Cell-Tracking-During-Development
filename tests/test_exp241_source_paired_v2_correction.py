"""Local, label-free regression checks for the exact EXP241 v1 SHA failure."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_exp241_source_paired_scorer_v2 as stage  # noqa: E402
import launch_exp241_source_paired_scorer_v2 as launch  # noqa: E402
import verify_exp241_source_paired_scorer_v2 as verify  # noqa: E402

V1 = ROOT / "work/exp241_source_paired_scorer_v1_20260927"
V2 = ROOT / "work/exp241_source_paired_scorer_v2_20260927"
ACTUAL_PRIOR_GATE = "735496f5cf6dca2e24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
ACTUAL_PRIOR_RESULT = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
V1_TYPO = "735496f5cf6d2a24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_actual_archived_prior_gate_is_pinned_across_v2_runner_and_handoff():
    assert sha(stage.V1_FAILURE) == "8cf1410b6f175b42c97344ad125713136577e68d9e3a84a9a56840333b2deb76"
    failure = stage.failure_gate()
    source_verified = json.loads((V2 / "source_inner_verified.json").read_text())
    config = json.loads((V2 / "config.json").read_text())
    graph = json.loads((V2 / "graph_verified.json").read_text())
    assert failure["remote"]["prior_gate_actual_sha256"] == ACTUAL_PRIOR_GATE
    assert source_verified["remote"]["gate_sha256"] == ACTUAL_PRIOR_GATE
    assert failure["remote"]["prior_result_sha256"] == ACTUAL_PRIOR_RESULT
    assert source_verified["remote"]["result_sha256"] == ACTUAL_PRIOR_RESULT
    assert config["source_inner_result_sha256"] == ACTUAL_PRIOR_RESULT
    assert config["source_inner_verified_sha256"] == sha(V2 / "source_inner_verified.json")
    assert config["graph_verified_receipt_sha256"] == sha(V2 / "graph_verified.json")
    assert config["graph_result_sha256"] == graph["remote"]["result_sha256"]
    assert config["graph_no_label_gate_sha256"] == graph["remote"]["no_label_gate_sha256"]
    assert config["graph_run"] == graph["run"]
    spec = importlib.util.spec_from_file_location("exp241_paired_v2", V2 / "score_exp241_source_paired.py")
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    assert runner.SOURCE_GATE_SHA == verify.SOURCE_GATE_SHA == stage.PRIOR_GATE_SHA == ACTUAL_PRIOR_GATE
    assert runner.SOURCE_RESULT_SHA == verify.SOURCE_RESULT_SHA == stage.PRIOR_RESULT_SHA == ACTUAL_PRIOR_RESULT
    assert runner.SOURCE_GATE_SHA != V1_TYPO
    assert stage.RUN.endswith("/runs/exp241_source_paired_scorer_v2_20260927")
    assert runner.OUTPUT.as_posix() == config["output"] == stage.RUN + "/output"
    assert launch.command()[2] == stage.CODE + "/score_exp241_source_paired.py"
    assert launch.command()[-1] == stage.MANIFEST_SHA


def test_v2_metric_runtime_and_exact_two_file_delta():
    old = json.loads((V1 / "manifest.json").read_text())
    new, config = stage.local_bundle()
    assert sha(V2 / "manifest.json") == stage.MANIFEST_SHA
    assert {n for n in old["files"] if old["files"][n] != new["files"][n]} == {
        "score_exp241_source_paired.py", "config.json"}
    old_runner = (V1 / "score_exp241_source_paired.py").read_bytes()
    expected = old_runner.replace(V1_TYPO.encode(), ACTUAL_PRIOR_GATE.encode())
    expected = expected.replace(b"exp241_source_paired_scorer_v1_20260927/output",
                                b"exp241_source_paired_scorer_v2_20260927/output")
    expected = expected.replace(b"SEALED_EXP241_SOURCE_PAIRED_SCORER_V1",
                                b"SEALED_EXP241_SOURCE_PAIRED_SCORER_V2")
    assert (V2 / "score_exp241_source_paired.py").read_bytes() == expected
    old_config = (V1 / "config.json").read_bytes()
    expected = old_config.replace(b"exp241_source_paired_scorer_v1_20260927/output",
                                  b"exp241_source_paired_scorer_v2_20260927/output")
    expected = expected.replace(b"SEALED_EXP241_SOURCE_PAIRED_SCORER_V1",
                                b"SEALED_EXP241_SOURCE_PAIRED_SCORER_V2")
    assert (V2 / "config.json").read_bytes() == expected
    assert all((V1 / n).read_bytes() == (V2 / n).read_bytes()
               for n in old["files"] if n not in {"score_exp241_source_paired.py", "config.json"})
    source_config = json.loads((V2 / "source_inner_config.json").read_text())
    assert source_config["organizer_commit"] == "075fc5f5a52d11077f9dc2b074644618f26939e2"
    assert source_config["tracksdata_commit"] == "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
    assert sha(V2 / "source_inner_config.json") == config["source_inner_config_sha256"]
    assert sha(V2 / "tracking_cellmot_official/metrics.py") == "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
    assert sha(V2 / "tracking_cellmot_official/division_metrics.py") == "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"
    stage.remote_preflight_source(False)
    stage.remote_stage_source(new)
    launch.remote_launch_source(new)
    remote_verifier = verify.remote_source("0" * 64, "0" * 64, "0" * 64)
    assert "root=pathlib.Path('/home/scientists/" in remote_verifier
    assert "\\\\home\\\\scientists" not in remote_verifier
