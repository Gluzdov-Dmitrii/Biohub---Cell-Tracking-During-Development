"""Local contract checks for the bounded EXP227 epoch-10-to-20 handoff."""
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
import launch_exp227_source_resume as launch  # noqa: E402
import prepare_exp227_source_resume as prepare  # noqa: E402
import run_exp227_source_resume as runner  # noqa: E402


def staged_text(source, marker):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "write_text" and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    if marker in value.value:
                        return value.value
    raise AssertionError(f"Generated stage lacks {marker}")


class ResumeContract(unittest.TestCase):
    def test_only_source44_epoch_11_to_20(self):
        parent = json.loads((ROOT / "reports/exp227_source_block02_plan_20260927.json").read_text())
        plan = {**parent, "purpose": "source_only_full_training_block03",
                "seed": 3407, "start_epoch": 11, "block_end_epoch": 20,
                "parent_completed_epochs": 10,
                "initial_output_root": runner.INITIAL_OUTPUT_ROOT,
                "parent_checkpoint": runner.PARENT_RUN + "/output/fold1/last.pt",
                "parent_checkpoint_sha256": runner.PARENT_CHECKPOINT_SHA,
                "parent_result_sha256": runner.PARENT_RESULT_SHA,
                "parent_history_sha256": "a" * 64,
                "output": runner.RUN + "/output"}
        runner.validate(plan)
        for change in ({"block_end_epoch": 21}, {"seed": 3406},
                       {"parent_checkpoint_sha256": "0" * 64},
                       {"source_embryo": "6bba"}):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                runner.validate({**plan, **change})
        bad = json.loads(json.dumps(plan))
        bad["train"][0]["dataset_id"] = "6bba_forbidden"
        with self.assertRaises(AssertionError):
            runner.validate(bad)

    def test_prepare_checks_parent_then_generates_a_parseable_stage(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "reports").mkdir()
            (root / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts/run_exp227_source_resume.py",
                         root / "scripts/run_exp227_source_resume.py")
            for stem in ("plan", "prepare", "config"):
                filename = f"exp227_source_block02_{stem}_20260927.json"
                shutil.copy2(ROOT / "reports" / filename, root / "reports" / filename)
            calls = []

            def fake_ssh(alias, command, source=None):
                calls.append((alias, command))
                if alias == "nsu-quadro":
                    return {"requests": [{"id": "exp227-horaz-source-block02-20260927",
                                          "state": "RELEASED", "run_path": runner.PARENT_RUN}]}
                ast.parse(source)
                if "PASS_EXP227_BLOCK03_PARENT_PREFLIGHT" in source:
                    return {"status": "PASS_EXP227_BLOCK03_PARENT_PREFLIGHT",
                            "checkpoint_sha256": runner.PARENT_CHECKPOINT_SHA,
                            "result_sha256": runner.PARENT_RESULT_SHA,
                            "history_sha256": "a" * 64}
                plan_text = staged_text(source, '"purpose": "source_only_full_training_block03"')
                runner_text = staged_text(source, "Exact source44 Horaz continuation")
                return {"status": "STAGED_EXP227_SOURCE_BLOCK03", "code": prepare.CODE,
                        "manifest_sha256": "b" * 64,
                        "plan_sha256": hashlib.sha256(plan_text.encode()).hexdigest(),
                        "runner_sha256": hashlib.sha256(runner_text.encode()).hexdigest()}

            with patch.object(prepare, "ROOT", root), patch.object(prepare, "ssh", fake_ssh):
                prepare.main()
            self.assertEqual(len(calls), 3)
            plan = json.loads((root / "reports/exp227_source_block03_plan_20260927.json").read_text())
            runner.validate(plan)
            self.assertEqual(plan["parent_history_sha256"], "a" * 64)
            receipt = json.loads((root / "reports/exp227_source_block03_prepare_20260927.json").read_text())
            self.assertEqual(receipt["stage"]["manifest_sha256"], "b" * 64)
            self.assertEqual(hashlib.sha256(
                (root / "reports/exp227_source_block03_plan_20260927.json").read_bytes()
            ).hexdigest(), receipt["stage"]["plan_sha256"])

    def test_prepare_rejects_unreleased_parent_before_stage(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "reports").mkdir()
            for stem in ("plan", "prepare", "config"):
                filename = f"exp227_source_block02_{stem}_20260927.json"
                shutil.copy2(ROOT / "reports" / filename, root / "reports" / filename)
            state = {"requests": [{"id": "exp227-horaz-source-block02-20260927",
                                   "state": "RUNNING", "run_path": runner.PARENT_RUN}]}
            with patch.object(prepare, "ROOT", root), patch.object(prepare, "ssh", return_value=state):
                with self.assertRaises(AssertionError):
                    prepare.main()
            self.assertFalse((root / "reports/exp227_source_block03_plan_20260927.json").exists())

    def test_failed_prelaunch_releases_only_when_run_absent(self):
        for run_exists in (False, True):
            with self.subTest(run_exists=run_exists), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                config_path = root / "config.json"
                prepare_path = root / "prepare.json"
                parent_path = root / "parent.json"
                config = {"experiment": "EXP227", "max_seconds": 21600,
                          "code": prepare.CODE, "run": runner.RUN,
                          "script": "run_exp227_source_resume.py",
                          "arguments": [prepare.CODE + "/plan.json", "--plan-sha256", "a" * 64],
                          "lease_id": "exp227-horaz-source-block03-20260927", "token": "token"}
                config_path.write_text(json.dumps(config))
                prepare_path.write_text(json.dumps({"status": "PREPARED_EXP227_SOURCE_BLOCK03_NO_TARGET_ACCESS",
                                                     "target_data_opened": False, "epochs": [11, 20],
                                                     "stage": {"code": prepare.CODE,
                                                               "plan_sha256": "a" * 64,
                                                               "manifest_sha256": "b" * 64}}))
                parent_path.write_text(json.dumps({"lease_id": "parent"}))
                calls = []

                def fake_ssh(alias, command, source=None):
                    calls.append((alias, command, source))
                    if command.endswith(" status"):
                        return {"requests": [{"id": "parent", "state": "RELEASED",
                                              "run_path": runner.PARENT_RUN}]}
                    if "--verified-stopped" in command:
                        return {"state": "RELEASED"}
                    if source and "run_exists" in source:
                        return {"run_exists": run_exists}
                    if source and "nvidia-smi" in source:
                        tree = ast.parse(source)
                        lines = source.splitlines()
                        self.assertLess(next(i for i, line in enumerate(lines) if "nvidia-smi" in line),
                                        next(i for i, line in enumerate(lines) if "run.mkdir" in line))
                        self.assertIsInstance(tree, ast.Module)
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
                releases = [command for _, command, _ in calls if "--verified-stopped" in command]
                self.assertEqual(len(releases), 0 if run_exists else 1)


if __name__ == "__main__":
    unittest.main()
