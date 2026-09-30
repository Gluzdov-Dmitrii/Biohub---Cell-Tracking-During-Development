import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_synthetic_gap_deepcenter import close_synthetic_gaps, refine_midpoint
from select_synthetic_gap_source_gate import evaluate_gate


class SyntheticGapDeepCenterTests(unittest.TestCase):
    def test_intensity_refinement_moves_toward_bright_voxel(self):
        frame = np.zeros((5, 9, 9), dtype=np.float32)
        frame[2, 5, 4] = 100.0
        midpoint = np.array([2.0, 4.0, 4.0])
        refined, status = refine_midpoint(midpoint, frame, np.ones(3))
        self.assertEqual(status, "refined")
        self.assertTrue(np.allclose(refined, [2.0, 5.0, 4.0]))

    def test_source_gate_requires_both_directions(self):
        def payload(base, raw, gated, checked=1, added=1):
            rows = lambda value: [{"dataset": "movie", "adj_edge_jaccard": value, "node_recall": 0.9}]
            return {
                "summary_by_arm": {
                    "registered_hungarian": {"score": base},
                    "synthetic_gap_no_veto": {"score": raw},
                    "synthetic_gap_deepcenter": {"score": gated},
                },
                "per_movie_by_arm": {
                    "registered_hungarian": rows(base),
                    "synthetic_gap_deepcenter": rows(gated),
                },
                "telemetry": [{"deepcenter": {
                    "deepcenter_checked": checked,
                    "synthetic_added": added,
                }}],
            }
        passed = evaluate_gate({"a": payload(.5, .50, .51), "b": payload(.4, .405, .41)})
        self.assertTrue(passed["eligible_for_reciprocal_target_oof"])
        failed = evaluate_gate({"a": payload(.5, .50, .51), "b": payload(.4, .405, .39)})
        self.assertFalse(failed["eligible_for_reciprocal_target_oof"])

    def test_heatmap_cache_avoids_duplicate_model_inference(self):
        coords = np.array([[0, 1, 2, 2], [2, 1, 2, 3]], dtype=np.float64)
        bundle = {"cfg": type("Cfg", (), {"pool_factor": 1})()}
        frame = np.ones((3, 7, 7), dtype=np.float32)
        heatmap = np.ones_like(frame)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            cache_dir = Path(tmp)
            with (
                patch("evaluate_synthetic_gap_deepcenter.read_zarr_meta", return_value=(frame.shape, frame.dtype)),
                patch("evaluate_synthetic_gap_deepcenter.get_frame", return_value=frame),
                patch("evaluate_synthetic_gap_deepcenter.deepcenter_heatmap", return_value=heatmap) as infer,
            ):
                _, _, first = close_synthetic_gaps(
                    coords,
                    [],
                    np.ones(3),
                    Path("movie.zarr"),
                    bundle,
                    deepcenter_confirm_min_span_um=0,
                    heatmap_cache_dir=cache_dir,
                )
                _, _, second = close_synthetic_gaps(
                    coords,
                    [],
                    np.ones(3),
                    Path("movie.zarr"),
                    bundle,
                    deepcenter_confirm_min_span_um=0,
                    heatmap_cache_dir=cache_dir,
                )
        self.assertEqual(infer.call_count, 1)
        self.assertEqual(first["deepcenter_heatmaps_inferred"], 1)
        self.assertEqual(second["deepcenter_heatmaps_loaded"], 1)


if __name__ == "__main__":
    unittest.main()
