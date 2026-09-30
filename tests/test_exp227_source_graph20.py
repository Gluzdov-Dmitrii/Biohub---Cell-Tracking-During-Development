"""Local gates for EXP227 epoch20 no-label source inference."""
import ast
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp227_source_graph20 as launch  # noqa: E402
import prepare_exp227_source_graph20 as prepare  # noqa: E402
import run_exp227_source_graph20 as runner  # noqa: E402


def staged_text(source, marker):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "write_text" and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    if marker in value.value:
                        return value.value
    raise AssertionError(f"Generated stage lacks {marker}")


class Graph20Contract(unittest.TestCase):
    def plan(self):
        old = json.loads((ROOT / "reports/exp227_source_graph10_plan_20260927.json").read_text())
        return {**old, "experiment": "EXP227_SOURCE_GRAPH20", "checkpoint_epoch": 20,
                "training_code_manifest_sha256": runner.TRAIN_MANIFEST_SHA,
                "training_plan_sha256": runner.TRAIN_PLAN_SHA,
                "training_run": runner.TRAIN_RUN,
                "checkpoint": runner.TRAIN_RUN + "/output/fold1/epoch_020.pt",
                "training_history_sha256": "a" * 64,
                "code": runner.CODE, "output": runner.RUN + "/output"}

    def test_exact_eight_source_ids_and_epoch20(self):
        plan = self.plan()
        runner.validate(plan)
        self.assertEqual([row["dataset"] for row in plan["movies"]], list(runner.INNER_IDS))
        for change in ({"checkpoint_epoch": 10}, {"training_plan_sha256": "0" * 64},
                       {"checkpoint": runner.TRAIN_RUN + "/output/fold1/last.pt"}):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                runner.validate({**plan, **change})
        bad = json.loads(json.dumps(plan))
        bad["movies"][0]["dataset"] = "6bba_forbidden"
        with self.assertRaises(AssertionError):
            runner.validate(bad)

    def test_audit_guard_denies_labels_target_and_other_images(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            guard = runner.no_labels_guard(root, runner.INNER_IDS)
            guard("open", (root / (runner.INNER_IDS[0] + ".zarr") / "0" / "zarr.json",))
            for path in (root / (runner.INNER_IDS[0] + ".geff") / "attributes.json",
                         root / "6bba_forbidden.zarr" / "0" / "zarr.json",
                         root / "44b6_unlisted.zarr" / "0" / "zarr.json"):
                with self.subTest(path=path), self.assertRaises(PermissionError):
                    guard("open", (path,))

    def test_prepare_requires_release_and_builds_hashed_plan(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "reports").mkdir()
            (root / "scripts").mkdir()
            for stem in ("prepare", "config"):
                filename = f"exp227_source_block03_{stem}_20260927.json"
                shutil.copy2(ROOT / "reports" / filename, root / "reports" / filename)
            for filename in ("run_exp227_source_graph20.py", "run_exp223_inference.py"):
                shutil.copy2(ROOT / "scripts" / filename, root / "scripts" / filename)
            movies = self.plan()["movies"]
            calls = []

            def fake_ssh(alias, command, source=None):
                calls.append((alias, command))
                if alias == "nsu-quadro":
                    return {"requests": [{"id": "exp227-horaz-source-block03-20260927",
                                          "state": "RELEASED", "run_path": runner.TRAIN_RUN}]}
                ast.parse(source)
                if "PASS_EXP227_SOURCE20_PARENT_PREFLIGHT" in source:
                    for requirement in ("TRAIN_PLAN_SHA", "periodic_checkpoint_sha256",
                                        "history_path", "supervision/control.json"):
                        if requirement == "TRAIN_PLAN_SHA":
                            self.assertIn(runner.TRAIN_PLAN_SHA, source)
                        else:
                            self.assertIn(requirement, source)
                    return {"status": "PASS_EXP227_SOURCE20_PARENT_PREFLIGHT",
                            "checkpoint_sha256": "c" * 64,
                            "training_result_sha256": "d" * 64,
                            "training_history_sha256": "e" * 64,
                            "movies": movies}
                plan_text = staged_text(source, '"experiment": "EXP227_SOURCE_GRAPH20"')
                infer_text = staged_text(source, "Freeze eight source-only Horaz epoch-20")
                return {"status": "STAGED_EXP227_SOURCE_GRAPH20", "code": prepare.CODE,
                        "manifest_sha256": "f" * 64,
                        "plan_sha256": hashlib.sha256(plan_text.encode()).hexdigest(),
                        "runner_sha256": hashlib.sha256(infer_text.encode()).hexdigest()}

            with patch.object(prepare, "ROOT", root), patch.object(prepare, "ssh", fake_ssh):
                prepare.main()
            self.assertEqual(len(calls), 3)
            plan_path = root / "reports/exp227_source_graph20_plan_20260927.json"
            plan = json.loads(plan_path.read_text())
            runner.validate(plan)
            receipt = json.loads((root / "reports/exp227_source_graph20_prepare_20260927.json").read_text())
            self.assertEqual(hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                             receipt["stage"]["plan_sha256"])
            self.assertEqual(plan["training_history_sha256"], "e" * 64)

    def test_prepare_stops_on_unreleased_parent(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "reports").mkdir()
            for stem in ("prepare", "config"):
                filename = f"exp227_source_block03_{stem}_20260927.json"
                shutil.copy2(ROOT / "reports" / filename, root / "reports" / filename)
            state = {"requests": [{"id": "exp227-horaz-source-block03-20260927",
                                   "state": "RUNNING", "run_path": runner.TRAIN_RUN}]}
            with patch.object(prepare, "ROOT", root), patch.object(prepare, "ssh", return_value=state):
                with self.assertRaises(AssertionError):
                    prepare.main()
            self.assertFalse((root / "reports/exp227_source_graph20_prepare_20260927.json").exists())

    def test_gpu_prelaunch_release_only_without_run(self):
        for run_exists in (False, True):
            with self.subTest(run_exists=run_exists), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                config_path = root / "config.json"
                prepare_path = root / "prepare.json"
                parent_path = root / "parent.json"
                config = {"experiment": "EXP227", "max_seconds": 3600,
                          "code": runner.CODE, "run": runner.RUN,
                          "script": "run_exp227_source_graph20.py",
                          "arguments": [runner.CODE + "/plan.json", "--plan-sha256", "a" * 64],
                          "lease_id": "exp227-source-graph20-v1-20260927", "token": "token"}
                config_path.write_text(json.dumps(config))
                prepare_path.write_text(json.dumps({"status": "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS",
                                                     "target_labels_read": False, "movies": 8,
                                                     "stage": {"code": runner.CODE,
                                                               "plan_sha256": "a" * 64,
                                                               "manifest_sha256": "b" * 64}}))
                parent_path.write_text(json.dumps({"lease_id": "parent"}))
                calls = []

                def fake_ssh(alias, command, source=None):
                    calls.append((alias, command))
                    if command.endswith(" status"):
                        return {"requests": [{"id": "parent", "state": "RELEASED",
                                              "run_path": runner.TRAIN_RUN}]}
                    if "--verified-stopped" in command:
                        return {"state": "RELEASED"}
                    if source and "run_exists" in source:
                        return {"run_exists": run_exists}
                    if source and "nvidia-smi" in source:
                        ast.parse(source)
                        lines = source.splitlines()
                        self.assertLess(next(i for i, line in enumerate(lines) if "nvidia-smi" in line),
                                        next(i for i, line in enumerate(lines) if "run.mkdir" in line))
                        raise RuntimeError("GPU occupied")
                    raise AssertionError("Unexpected SSH call")

                with ExitStack() as stack:
                    stack.enter_context(patch.object(launch, "CONFIG", config_path))
                    stack.enter_context(patch.object(launch, "PREPARE", prepare_path))
                    stack.enter_context(patch.object(launch, "PARENT_CONFIG", parent_path))
                    stack.enter_context(patch.object(launch, "ssh", fake_ssh))
                    stack.enter_context(patch.object(launch, "queue_request", return_value={
                        "state": "RESERVED", "gpus": ["GPU-test"], "alias": "nsu-a100"}))
                    with self.assertRaisesRegex(RuntimeError, "GPU occupied"):
                        launch.main()
                releases = [command for _, command in calls if "--verified-stopped" in command]
                self.assertEqual(len(releases), 0 if run_exists else 1)


if __name__ == "__main__":
    unittest.main()
