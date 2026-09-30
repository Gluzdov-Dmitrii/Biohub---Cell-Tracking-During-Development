"""Target inference must use the frozen source choice and exact opposite cohort."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_exp234_target_chunk import validate_plan


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    return write(path, json.dumps(value))


class TargetPlanTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        code = root / "code"
        code.mkdir()
        roles = {}
        for role in ("primary", "secondary", "center"):
            path = root / (role + ".bin")
            roles[role] = {"path": str(path), "sha256": write(path, role)}
        source_bundle = {"source_embryo": "44b6", "source_train_movies": ["44b6_train"],
                         "source_validation_movies": ["44b6_validation"],
                         "center_seen_movies": ["44b6_center"], **roles}
        bundle = {**source_bundle, "evaluation_mode": "EXP234_TARGET_ROLLOUT"}
        source_path = root / "source_bundle.json"
        bundle_path = code / "bundle.json"
        source_sha = write_json(source_path, source_bundle)
        bundle_sha = write_json(bundle_path, bundle)
        chunks = []
        start = 0
        for size in [15] * 4 + [14] * 4:
            chunks.append([f"6bba_{j:08d}" for j in range(start, start + size)])
            start += size
        assignment_path = code / "assignment.json"
        assignment = {"status": "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS",
                      "canonical_cohort_manifest_sha256": "cohort-sha",
                      "directions": {"44b6": {"target_embryo": "6bba", "chunks": chunks}}}
        assignment_sha = write_json(assignment_path, assignment)
        movie_path = code / "movies.json"
        movie_sha = write_json(movie_path, chunks[0])
        selection_path = root / "selection.json"
        selection_sha = write_json(selection_path, {"status": "PASS_EXP234_SOURCE_THRESHOLD_SELECTED",
                                                    "source_embryo": "44b6", "selected_threshold": "0.940"})
        notebook_path = root / "notebook.ipynb"
        notebook_sha = write(notebook_path, "{}")
        write_json(code / "code_manifest.json", {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (assignment_path, movie_path, bundle_path)})
        self.primary_path = Path(roles["primary"]["path"])
        self.plan = {"experiment": "EXP234_TARGET_CHUNK", "source_embryo": "44b6",
                     "target_embryo": "6bba", "chunk_count": 8, "chunk_index": 0,
                     "selected_threshold": "0.940", "code": str(code), "cohort_sha256": "cohort-sha",
                     "assignment": str(assignment_path), "assignment_sha256": assignment_sha,
                     "movies": str(movie_path), "movies_sha256": movie_sha,
                     "source_selection_result": str(selection_path),
                     "source_selection_result_sha256": selection_sha,
                     "source_bundle": str(source_path), "source_bundle_sha256": source_sha,
                     "bundle": str(bundle_path), "bundle_sha256": bundle_sha,
                     "notebook": str(notebook_path), "notebook_sha256": notebook_sha}

    def test_exact_frozen_source_choice_passes(self):
        _, _, movies = validate_plan(self.plan)
        self.assertEqual(len(movies), 15)

    def test_target_threshold_cannot_differ_from_source_choice(self):
        self.plan["selected_threshold"] = "0.900"
        with self.assertRaises(AssertionError):
            validate_plan(self.plan)

    def test_changed_weight_bytes_block_target_inference(self):
        self.primary_path.write_text("changed")
        with self.assertRaises(AssertionError):
            validate_plan(self.plan)


if __name__ == "__main__":
    unittest.main()
