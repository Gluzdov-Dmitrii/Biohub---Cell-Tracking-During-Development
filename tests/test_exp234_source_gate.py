"""EXP234 must reject incomplete or changed source-validation arms before labels."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_exp234_source_threshold import gate, THRESHOLDS
from exp234_source_scope import reject_label_geff_open
from run_exp234_source_scorer_guarded import released_success


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path, value):
    return write(path, json.dumps(value))


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        code, run = root / "code", root / "run"
        code.mkdir(); run.mkdir()
        self.movies = [f"44b6_{i:08d}" for i in range(8)]
        roles = {}
        for name in ("primary", "secondary", "center"):
            model = root / (name + ".bin")
            roles[name] = {"path": str(model), "sha256": write(model, name)}
        bundle = {"source_embryo": "44b6", "evaluation_mode": "EXP234_SOURCE_THRESHOLD_SELECTION",
                  "selection_rule": "maximum_official_source_score_tie_baseline_0965",
                  "source_validation_movies": self.movies,
                  "source_train_movies": ["44b6_train"], "center_seen_movies": [], **roles}
        bundle_path, movie_path = code / "44b6_bundle.json", code / "44b6_movies.json"
        bundle_sha, movies_sha = json_write(bundle_path, bundle), json_write(movie_path, self.movies)
        plan = {"experiment": "EXP234", "source_embryo": "44b6",
                "notebook_sha256": "notebook-sha-fixture",
                "thresholds": list(THRESHOLDS), "bundle": str(bundle_path), "bundle_sha256": bundle_sha,
                "movies": str(movie_path), "movies_sha256": movies_sha, "movie_count": 8}
        plan_path = code / "44b6_plan.json"
        self.plan_sha = json_write(plan_path, plan)
        manifest_path = code / "code_manifest.json"
        manifest_sha = json_write(manifest_path, {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (bundle_path, movie_path, plan_path)})
        records = []
        for threshold in THRESHOLDS:
            arm = run / "output" / ("threshold_" + threshold.replace(".", ""))
            csv_path = arm / "submission.csv"
            header = "id,dataset,row_type,node_id,t,z,y,x,source_id,target_id\n"
            rows = [f"{i},{movie},node,1,0,0,0,0,-1,-1\n" for i, movie in enumerate(self.movies)]
            csv_sha = write(csv_path, header + "".join(rows))
            receipt_path = arm / "inference_receipt.json"
            receipt_sha = json_write(receipt_path, {"target_labels_read": False,
                "notebook_sha256": plan["notebook_sha256"],
                "base_predictor_sha256": "c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9",
                "submission_sha256": csv_sha, "override_env": {"BIOHUB_DET_THRESHOLD": threshold},
                "movies": self.movies, "bundle": bundle})
            records.append({"threshold": threshold, "csv": str(csv_path),
                            "csv_sha256": csv_sha, "receipt_sha256": receipt_sha})
        json_write(run / "exit.json", {"returncode": 0, "hard_timeout": False})
        json_write(run / "output/status.json", {"status": "PASS_EXP234_SOURCE_ARMS_NO_LABELS",
            "target_labels_read": False, "movies": self.movies, "plan_sha256": self.plan_sha,
            "thresholds": list(THRESHOLDS), "records": records})
        self.config = {"run": str(run), "inference_code": str(code),
                       "source_embryo": "44b6", "plan_sha256": self.plan_sha,
                       "inference_manifest_sha256": manifest_sha,
                       "expected_movies": self.movies,
                       "expected_model_shas": {role: roles[role]["sha256"] for role in roles}}

    def test_complete_arm_gate(self):
        graphs, receipt = gate(self.config)
        self.assertEqual(set(graphs), set(THRESHOLDS))
        self.assertEqual(receipt["status"], "PASS_ALL_EXP234_SOURCE_ARMS_BEFORE_LABEL_ACCESS")

    def test_missing_arm_blocks_gate(self):
        status = Path(self.config["run"]) / "output/status.json"
        value = json.loads(status.read_text()); value["records"].pop()
        json_write(status, value)
        with self.assertRaises(AssertionError):
            gate(self.config)

    def test_changed_csv_blocks_gate(self):
        csv_path = Path(self.config["run"]) / "output/threshold_0900/submission.csv"
        csv_path.write_text(csv_path.read_text() + "\n")
        with self.assertRaises(AssertionError):
            gate(self.config)

    def test_mutated_bundle_blocks_gate(self):
        bundle_path = Path(self.config["inference_code"]) / "44b6_bundle.json"
        bundle = json.loads(bundle_path.read_text()); bundle["center_seen_movies"] = [self.movies[0]]
        json_write(bundle_path, bundle)
        with self.assertRaises(AssertionError):
            gate(self.config)

    def test_changed_expected_cohort_blocks_gate(self):
        self.config["expected_movies"] = list(reversed(self.movies))
        with self.assertRaises(AssertionError):
            gate(self.config)

    def test_inference_geff_audit_allows_only_generated_predictions(self):
        root = Path(self.temp.name)
        predictions = root / "run/output/threshold_0900/tracking_repo/predictions"
        generated = predictions / "user/model/split_0/44b6_a.geff/nodes/zarr.json"
        label = root / "data/44b6_a.geff/nodes/zarr.json"
        other_run = root / "other/predictions/44b6_a.geff/nodes/zarr.json"
        reject_label_geff_open("open", (generated, "r", 0), predictions)
        reject_label_geff_open("open", (str(generated).encode(), "r", 0), predictions)
        reject_label_geff_open("other", (label, "r", 0), predictions)
        reject_label_geff_open("open", (root / "data/44b6_a.zarr/zarr.json", "r", 0), predictions)
        for forbidden in (label, other_run):
            with self.assertRaisesRegex(RuntimeError, "no label access"):
                reject_label_geff_open("open", (forbidden, "r", 0), predictions)

    def test_guarded_source_scorer_requires_verified_release(self):
        state = {"monitor_status": "RELEASED_AFTER_VERIFIED_EXIT",
                 "queue": {"state": "RELEASED"},
                 "exit": {"returncode": 0, "hard_timeout": False},
                 "identity_alive": False, "group_alive": False, "gpu_pids": [],
                 "status": {"status": "PASS_EXP234_SOURCE_ARMS_NO_LABELS"}}
        self.assertTrue(released_success(state))
        for changed in ({"monitor_status": "MONITORING"},
                        {"queue": {"state": "RUNNING"}},
                        {"exit": {"returncode": 1, "hard_timeout": False}},
                        {"identity_alive": True}, {"gpu_pids": [123]},
                        {"status": None}):
            with self.subTest(changed=changed):
                self.assertFalse(released_success({**state, **changed}))


if __name__ == "__main__":
    unittest.main()
