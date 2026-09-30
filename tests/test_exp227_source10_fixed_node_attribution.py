"""Synthetic contracts for the pinned source-only fixed-node diagnostic."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_exp227_source10_fixed_node_ceiling as analysis  # noqa: E402
import run_exp227_source10_fixed_node_attribution_remote as launch  # noqa: E402


class AttributionContract(unittest.TestCase):
    def test_endpoint_association_and_fp_partition(self):
        row = analysis.edge_decomposition(
            pred_edges=[(10, 20), (20, 30)], gt_edges=[(1, 2), (2, 3)],
            pred_to_gt={10: 1, 20: 2}, gt_to_pred={1: 10, 2: 20})
        self.assertEqual(row["edge_tp"], 1)
        self.assertEqual(row["fn_missing_target_endpoint"], 1)
        self.assertEqual(row["fp_source_anchor_target_unmatched"], 1)
        self.assertEqual(analysis.partition(row), (1, 0, 1))
        missing = analysis.edge_decomposition(
            pred_edges=[], gt_edges=[(1, 2)],
            pred_to_gt={10: 1, 20: 2}, gt_to_pred={1: 10, 2: 20})
        self.assertEqual(analysis.partition(missing), (0, 1, 0))

    def test_optimistic_bound_keeps_endpoint_and_node_penalty(self):
        self.assertAlmostEqual(analysis.optimistic_adjusted_edge(10, 2, 0.5), 0.76)
        self.assertEqual(analysis.optimistic_adjusted_edge(10, 10, 0.5), 0.0)
        with self.assertRaises(AssertionError):
            analysis.optimistic_adjusted_edge(10, 11, 0.0)

    def test_guard_rejects_target_and_other_geff(self):
        allowed = analysis.DATA / (analysis.SOURCE_IDS[0] + ".geff") / "zarr.json"
        analysis.source_guard("open", (allowed,))
        for path in (analysis.DATA / "6bba_forbidden.geff" / "zarr.json",
                     analysis.DATA / "44b6_unlisted.geff" / "zarr.json",
                     analysis.DATA / "44b6_unlisted.zarr" / "0" / "zarr.json"):
            with self.subTest(path=path), self.assertRaises(PermissionError):
                analysis.source_guard("open", (path,))

    def test_remote_launcher_writes_only_successful_report(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "analysis.py"
            source.write_text("print('{}')\n")
            report = root / "report.json"
            failure = root / "failure.json"
            result = {"status": "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION",
                      "target6bba_access": False, "candidate_tuning": False,
                      "rows": [{}] * 8, "source_score": analysis.SOURCE_SCORE,
                      "optimistic": {"fixed_node_adjusted_edge_ceiling": 0.9},
                      "pooled": {key: 0 for key in
                                 ("gt_edges", "edge_fn", "endpoint_limited_fn",
                                  "association_limited_fn", "edge_fp", "division_tp",
                                  "division_fp", "division_fn")}}

            def fake_run(command, **kwargs):
                self.assertIn("CUDA_VISIBLE_DEVICES=", command[-1])
                self.assertIn("taskset -c 24-27", command[-1])
                self.assertEqual(kwargs["input"], source.read_text())
                return type("Completed", (), {"returncode": 0,
                                               "stdout": json.dumps(result), "stderr": ""})()

            with patch.object(launch, "ROOT", root), patch.object(launch, "SOURCE", source), \
                 patch.object(launch, "REPORT", report), patch.object(launch, "FAILURE", failure), \
                 patch.object(launch.subprocess, "run", fake_run), redirect_stdout(io.StringIO()):
                launch.main()
            saved = json.loads(report.read_text())
            self.assertEqual(saved["status"], result["status"])
            self.assertEqual(saved["execution"]["cuda_visible_devices"], "")
            self.assertFalse(failure.exists())

    def test_remote_failure_preserves_error_without_score_report(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "analysis.py"
            source.write_text("raise RuntimeError()\n")
            report = root / "report.json"
            failure = root / "failure.json"
            failed = type("Completed", (), {"returncode": 1,
                                            "stdout": "", "stderr": "source-only test failure"})()
            with patch.object(launch, "ROOT", root), patch.object(launch, "SOURCE", source), \
                 patch.object(launch, "REPORT", report), patch.object(launch, "FAILURE", failure), \
                 patch.object(launch.subprocess, "run", return_value=failed):
                with self.assertRaises(RuntimeError):
                    launch.main()
            self.assertFalse(report.exists())
            self.assertEqual(json.loads(failure.read_text())["status"],
                             "FAILED_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION")


if __name__ == "__main__":
    unittest.main()
