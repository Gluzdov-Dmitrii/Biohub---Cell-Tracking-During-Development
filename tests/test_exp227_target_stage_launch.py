"""Local mocks for immutable target stage and one-shot fair A100 launch."""
import ast
from contextlib import ExitStack
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp227_target_chunk as launch  # noqa: E402
import prepare_exp227_target_chunk0_local as prepare  # noqa: E402
import stage_exp227_target_chunk as stage  # noqa: E402
from tests.test_exp227_target_chunk_prepare import mock_selection  # noqa: E402


class StageLaunchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.index = 0
        self.destination = {**prepare.paths(0),
                            "bundle": self.root / "bundle",
                            "receipt": self.root / "prepare.json"}
        self.staged_paths = {"stage": self.root / "stage.json",
                             "config": self.root / "config.json"}
        self.launch_paths = {key: self.root / (key + ".json") for key in (
            "reservation", "partial", "launch", "prelaunch_release")}
        self.selection = mock_selection()
        self.prereg_sha = prepare.sha(prepare.PREREG)
        self.selection["prereg_sha256"] = self.prereg_sha
        self.selection_bytes = (json.dumps(self.selection, indent=2) + "\n").encode()
        self.selection_path = self.root / "selection.json"
        self.selection_path.write_bytes(self.selection_bytes)
        assignment_bytes = prepare.ASSIGNMENT.read_bytes()
        assignment = json.loads(assignment_bytes)
        built = prepare.build_bundle(self.selection, assignment, self.destination["bundle"],
                                     self.selection_bytes, assignment_bytes, self.prereg_sha)
        self.built = built
        prepared = {"status": "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY",
                    "chunk_index": 0, "bundle": str(self.destination["bundle"]),
                    "bundle_manifest_sha256": built["bundle_manifest_sha256"],
                    "plan_sha256": built["manifest"]["plan.json"],
                    "selection_sha256": hashlib.sha256(self.selection_bytes).hexdigest(),
                    "assignment_sha256": prepare.ASSIGNMENT_SHA,
                    "prereg_sha256": self.prereg_sha, "movies": built["plan"]["movies"],
                    "selected_epoch": 20, "checkpoint_sha256": self.selection["checkpoint_sha256"],
                    "code": self.destination["code"], "run": self.destination["run"],
                    "lease_id": self.destination["lease_id"],
                    "remote_stage_created": False, "remote_run_created": False,
                    "gpu_claimed": False, "target_labels_read": False}
        self.destination["receipt"].write_text(json.dumps(prepared) + "\n")

    def stage_patches(self):
        stack = ExitStack()
        stack.enter_context(patch.object(stage, "paths", return_value=self.destination))
        stack.enter_context(patch.object(stage, "stage_paths", return_value=self.staged_paths))
        stack.enter_context(patch.object(stage, "SELECTION", self.selection_path))
        return stack

    def fake_stage_ssh(self, alias, command, source=None):
        self.assertEqual(alias, "nsu-a100")
        self.assertEqual(command, "python3 -")
        ast.parse(source)
        if "PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT" in source:
            self.assertIn("assert not target.exists() and not run.exists()", source)
            return {"status": "PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT",
                    "parent_manifest_sha256": self.selection["epochs"][1]["graph_manifest_sha256"],
                    "checkpoint_sha256": self.selection["checkpoint_sha256"]}
        self.assertIn("shutil.copytree(source,target)", source)
        self.assertIn("assert body.count(old)==1", source)
        return {"status": "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS",
                "code": self.destination["code"], "run": self.destination["run"],
                "manifest_sha256": "f" * 64,
                "plan_sha256": self.built["manifest"]["plan.json"],
                "runner_sha256": self.built["manifest"]["run_exp227_target_chunk.py"],
                "selection_sha256": self.built["manifest"]["selection.json"],
                "assignment_sha256": self.built["manifest"]["assignment.json"]}

    def create_stage(self):
        with self.stage_patches(), patch.object(stage, "ssh", self.fake_stage_ssh):
            return stage.stage_index(0)

    def launcher_patches(self):
        stack = ExitStack()
        stack.enter_context(patch.object(launch, "paths", return_value=self.destination))
        stack.enter_context(patch.object(launch, "stage_paths", return_value=self.staged_paths))
        stack.enter_context(patch.object(launch, "launch_paths", return_value=self.launch_paths))
        return stack

    def test_stage_local_bundle_to_immutable_remote_recipe_only(self):
        receipt = self.create_stage()
        self.assertEqual(receipt["manifest_sha256"], "f" * 64)
        self.assertEqual(receipt["plan_sha256"], self.built["manifest"]["plan.json"])
        self.assertFalse(receipt["remote_run_created"])
        self.assertFalse(receipt["gpu_claimed"])
        self.assertEqual(json.loads(self.staged_paths["config"].read_text())["script"],
                         "run_exp227_target_chunk.py")
        with self.stage_patches(), patch.object(stage, "ssh", self.fake_stage_ssh):
            with self.assertRaises(AssertionError):
                stage.stage_index(0)

    def test_generated_stage_executes_against_local_parent_without_gpu(self):
        parent = self.root / "mock_parent_code"
        parent.mkdir()
        old = self.built["recipe"]["wrapper_old_assertion"]
        wrapper = parent / "exp227_job.py"
        wrapper.write_text("def main(config):\n    " + old + "\n")
        (parent / "code_manifest.json").write_text(json.dumps({
            "exp227_job.py": stage.sha(wrapper)}) + "\n")
        recipe = dict(self.built["recipe"], copy_parent_code=str(parent),
                      parent_manifest_sha256=stage.sha(parent / "code_manifest.json"))
        destination = dict(self.destination, code=str(self.root / "staged_code"),
                           run=str(self.root / "uncreated_run"))
        weight = self.root / "source_checkpoint.pt"
        weight.write_bytes(b"immutable source-only checkpoint")
        chosen = {"graph_code": str(parent),
                  "graph_manifest_sha256": recipe["parent_manifest_sha256"],
                  "checkpoint": str(weight), "checkpoint_sha256": stage.sha(weight)}
        preflight = stage.remote_preflight_source(destination, chosen)
        ast.parse(preflight)
        preflight_out = io.StringIO()
        with redirect_stdout(preflight_out):
            exec(compile(preflight, "<local-preflight-simulation>", "exec"), {})
        self.assertEqual(json.loads(preflight_out.getvalue()), {
            "status": "PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT",
            "parent_manifest_sha256": recipe["parent_manifest_sha256"],
            "checkpoint_sha256": stage.sha(weight)})
        names = recipe["overlay_files"]
        transfer = {name: (self.destination["bundle"] / name).read_bytes() for name in names}
        expected = {name: self.built["manifest"][name] for name in names}
        source = stage.remote_stage_source(destination, recipe, expected, transfer)
        ast.parse(source)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exec(compile(source, "<local-stage-simulation>", "exec"), {})
        result = json.loads(stdout.getvalue())
        staged = Path(destination["code"])
        self.assertEqual(result["status"], "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS")
        self.assertFalse(Path(destination["run"]).exists())
        self.assertIn(recipe["wrapper_new_assertion"], (staged / "exp227_job.py").read_text())
        self.assertNotIn(old, (staged / "exp227_job.py").read_text())
        manifest = json.loads((staged / "code_manifest.json").read_text())
        self.assertEqual(manifest["run_exp227_target_chunk.py"],
                         self.built["manifest"]["run_exp227_target_chunk.py"])
        self.assertTrue((staged / "code_manifest.json").read_bytes().endswith(b"\n"))
        self.assertEqual(stage.sha(staged / "code_manifest.json"), result["manifest_sha256"])
        local_plan = json.loads((staged / "plan.json").read_text())
        local_plan.update(code=destination["code"], output=str(Path(destination["run"]) / "output"),
                          checkpoint=str(weight), checkpoint_sha256=stage.sha(weight))
        (staged / "plan.json").write_text(json.dumps(local_plan) + "\n")
        manifest["plan.json"] = stage.sha(staged / "plan.json")
        (staged / "code_manifest.json").write_text(json.dumps(manifest) + "\n")
        stage_record = {"manifest_sha256": stage.sha(staged / "code_manifest.json"),
                        "plan_sha256": stage.sha(staged / "plan.json"),
                        "selection_sha256": stage.sha(staged / "selection.json"),
                        "checkpoint_sha256": stage.sha(weight),
                        "movies": local_plan["movies"]}
        config = {"run": destination["run"], "code": destination["code"],
                  "gpu": "GPU-test", "chunk_index": 0}
        launch_preflight = launch.preflight_source(stage_record, config)
        ast.parse(launch_preflight)
        launch_preflight_out = io.StringIO()
        with redirect_stdout(launch_preflight_out):
            exec(compile(launch_preflight, "<local-launch-preflight>", "exec"), {})
        self.assertEqual(json.loads(launch_preflight_out.getvalue()), {
            "status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
            "manifest_sha256": stage_record["manifest_sha256"],
            "plan_sha256": stage_record["plan_sha256"], "run_absent": True})
        launch_script = launch.launch_source(config, {
            "manifest_sha256": stage_record["manifest_sha256"],
            "plan_sha256": stage_record["plan_sha256"]})
        ast.parse(launch_script)
        launch_out = io.StringIO()
        with patch("subprocess.check_output", return_value=""), \
                patch("subprocess.Popen", side_effect=[SimpleNamespace(pid=101),
                                                        SimpleNamespace(pid=102)]), \
                redirect_stdout(launch_out):
            exec(compile(launch_script, "<local-launch-simulation>", "exec"), {})
        self.assertEqual(json.loads(launch_out.getvalue()), {"wrapper": 101, "observe": 102})
        config_path = Path(destination["run"]) / "config.json"
        self.assertTrue(config_path.read_bytes().endswith(b"\n"))
        self.assertEqual(json.loads(config_path.read_text()), config)

    def test_foreign_waiting_blocks_before_queue_claim_then_fair_launch(self):
        staged = self.create_stage()
        calls = []
        foreign = {"requests": [{"id": "foreign", "state": "WAITING_RESOURCE",
                                 "project": "kaggriculture", "gpus": []}]}

        def blocked_ssh(alias, command, source=None):
            calls.append((alias, command))
            if source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
                ast.parse(source)
                return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                        "manifest_sha256": staged["manifest_sha256"],
                        "plan_sha256": staged["plan_sha256"], "run_absent": True}
            if alias == "nsu-quadro":
                return foreign
            if source == launch.PHYSICAL_IDLE_SOURCE:
                return {"all_gpus": ["GPU-A", "GPU-B"], "busy_gpus": [],
                        "idle_gpus": ["GPU-A", "GPU-B"]}
            raise AssertionError("unexpected SSH")

        with self.launcher_patches(), patch.object(launch, "ssh", blocked_ssh), \
                patch.object(launch, "queue_request") as claim:
            with self.assertRaisesRegex(AssertionError, "Foreign project"):
                launch.launch_index(0)
            claim.assert_not_called()
        self.assertFalse(self.launch_paths["reservation"].exists())

        lease = {"state": "RESERVED", "id": self.destination["lease_id"],
                 "alias": "nsu-a100", "run_path": self.destination["run"],
                 "owner": "biohub-agent", "token": self.destination["token"],
                 "project": "biohub-cell-tracking-during-development", "gpus": ["GPU-B"]}

        def good_ssh(alias, command, source=None):
            if source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
                ast.parse(source)
                return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                        "manifest_sha256": staged["manifest_sha256"],
                        "plan_sha256": staged["plan_sha256"], "run_absent": True}
            if source == launch.PHYSICAL_IDLE_SOURCE:
                return {"all_gpus": ["GPU-A", "GPU-B"], "busy_gpus": ["GPU-A"],
                        "idle_gpus": ["GPU-B"]}
            if alias == "nsu-quadro" and command.endswith(" status"):
                return {"requests": [{"id": "other", "state": "RUNNING",
                                      "project": "kaggriculture", "gpus": ["GPU-A"],
                                      "run_path": "/other"}]}
            if source and "Reserved GPU has a compute process" in source:
                ast.parse(source)
                return {"wrapper": 100, "observe": 101}
            if source and "controller_pid" in source:
                ast.parse(source)
                return {"controller_pid": 102}
            raise AssertionError((alias, command))

        with self.launcher_patches(), patch.object(launch, "ssh", good_ssh), \
                patch.object(launch, "queue_request", return_value=lease) as claim:
            receipt = launch.launch_index(0)
            claim.assert_called_once()
        self.assertEqual(receipt["status"], "LAUNCHED_EXP227_TARGET6BBA_CHUNK")
        self.assertFalse(receipt["target_labels_read"])
        self.assertEqual(receipt["lease"]["gpus"], ["GPU-B"])
        self.assertEqual(receipt["fair_proof"]["first_fair_idle_gpu"], "GPU-B")
        self.assertEqual(receipt["control"]["controller_pid"], 102)
        with self.launcher_patches(), patch.object(launch, "ssh", good_ssh):
            with self.assertRaisesRegex(AssertionError, "Existing launch artifact"):
                launch.launch_index(0)

    def test_wrong_gpu_reservation_releases_only_after_no_run_proof(self):
        staged = self.create_stage()
        lease = {"state": "RESERVED", "id": self.destination["lease_id"],
                 "alias": "nsu-a100", "run_path": self.destination["run"],
                 "owner": "biohub-agent", "token": self.destination["token"],
                 "project": "biohub-cell-tracking-during-development", "gpus": ["GPU-A"]}
        calls = []

        def fake_ssh(alias, command, source=None):
            calls.append((alias, command))
            if source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
                return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                        "manifest_sha256": staged["manifest_sha256"],
                        "plan_sha256": staged["plan_sha256"], "run_absent": True}
            if source == launch.PHYSICAL_IDLE_SOURCE:
                return {"all_gpus": ["GPU-A", "GPU-B"], "busy_gpus": ["GPU-A"],
                        "idle_gpus": ["GPU-B"]}
            if alias == "nsu-quadro" and command.endswith(" status"):
                return {"requests": []}
            if source and "run_exists" in source:
                return {"run_exists": False}
            if alias == "nsu-quadro" and " release " in command:
                return {"state": "RELEASED", "id": self.destination["lease_id"]}
            raise AssertionError((alias, command))

        with self.launcher_patches(), patch.object(launch, "ssh", fake_ssh), \
                patch.object(launch, "queue_request", return_value=lease):
            with self.assertRaisesRegex(AssertionError, "fair physical-idle"):
                launch.launch_index(0)
        self.assertTrue(self.launch_paths["reservation"].exists())
        self.assertTrue(self.launch_paths["prelaunch_release"].exists())
        self.assertFalse(self.launch_paths["partial"].exists())
        self.assertEqual(sum(" release " in command for _, command in calls), 1)


if __name__ == "__main__":
    unittest.main()
