"""Local-only EXP236 reciprocal rollout and generated-source checks."""
import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import coordinate_exp236_target44b6 as coord  # noqa: E402
import launch_exp236_target_chunk as launch  # noqa: E402
import prepare_exp236_target_chunk_local as prepare  # noqa: E402
import run_exp236_target_chunk as runner  # noqa: E402
import stage_exp236_target_chunk as stage  # noqa: E402


def execute(source):
    ast.parse(source)
    output = io.StringIO()
    with redirect_stdout(output):
        exec(compile(source, "<fake-remote-source>", "exec"), {})
    return json.loads(output.getvalue())


class LocalRolloutTests(unittest.TestCase):
    def test_exact_source_and_all_four_local_bundles(self):
        frozen = coord.frozen_inputs()
        self.assertEqual([len(chunk) for chunk in frozen["chunks"]], [15, 15, 15, 14])
        self.assertEqual(sum(map(len, frozen["chunks"])), 59)
        self.assertEqual(frozen["checkpoint_sha256"], runner.CHECKPOINT_SHA)
        self.assertEqual(prepare.sha(prepare.PREREG), runner.PREREG_SHA)
        for index in range(4):
            prepared, plan, recipe, manifest = stage.local_gate(index)
            self.assertEqual(plan["movies"], frozen["chunks"][index])
            self.assertEqual(prepared["checkpoint_sha256"], runner.CHECKPOINT_SHA)
            self.assertEqual(recipe["copy_parent_code"], runner.SOURCE_GRAPH_CODE)
            self.assertEqual(manifest["source_handoff.json"], runner.HANDOFF_SHA)
            self.assertFalse(prepared["remote_stage_created"])
            self.assertFalse(prepared["gpu_claimed"])

    def test_audit_hook_rejects_labels_replay_and_unassigned_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            guard = runner.no_labels_guard(root, ["44b6_00000001"])
            allowed = root / "44b6_00000001.zarr" / "0" / "zarr.json"
            guard("open", (str(allowed),))
            for name in ("44b6_00000002.zarr/0/zarr.json",
                         "6bba_00000001.zarr/0/zarr.json", "labels.geff/data",
                         "submission.csv"):
                with self.subTest(name=name), self.assertRaises(PermissionError):
                    guard("open", (str(root / name),))

    def test_runner_validates_exact_dynamic_assignment_and_source_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "code" / "exp236_target44b6_chunk00_v1_20260927"
            shutil.copytree(prepare.paths(0)["bundle"], code)
            plan = json.loads((code / "plan.json").read_text())
            plan["code"] = code.as_posix()
            plan["output"] = (root / "runs" / "exp236_target44b6_chunk00_v1_20260927" / "output").as_posix()
            plan["data_root"] = (root / "data" / "exp213_source_view_20260912").as_posix()
            for key in ("assignment", "source_training", "source_handoff",
                        "source_score", "source_graph_plan"):
                plan[key] = (code / (key + ".json")).as_posix()
            with patch.object(runner, "REMOTE", root.as_posix()), \
                 patch.object(runner, "DATA_ROOT", plan["data_root"]):
                runner.validate_plan(plan)
                corrupted = dict(plan, movies=plan["movies"][1:])
                with self.assertRaises(AssertionError):
                    runner.validate_plan(corrupted)
                corrupted = dict(plan, checkpoint_sha256="0" * 64)
                with self.assertRaises(AssertionError):
                    runner.validate_plan(corrupted)

    def test_generated_stage_and_launch_sources_run_only_in_fake_workspace(self):
        _, plan, recipe, manifest = stage.local_gate(0)
        bundle = prepare.paths(0)["bundle"]
        files = {name: (bundle / name).read_bytes() for name in recipe["overlay_files"]}
        transfer = {name: manifest[name] for name in recipe["overlay_files"]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent, target, run = root / "parent", root / "target", root / "run"
            parent.mkdir()
            checkpoint = root / "last.pt"
            checkpoint.write_bytes(b"sealed fake checkpoint")
            (parent / "plan.json").write_text("{}\n")
            (parent / "exp227_job.py").write_text(
                "assert config['script'] == 'run_exp236_source_graph10_v2.py'\n")
            parent_manifest = {path.name: prepare.sha(path) for path in parent.iterdir()}
            (parent / "code_manifest.json").write_text(json.dumps(parent_manifest) + "\n")
            fake_recipe = {**recipe, "copy_parent_code": str(parent),
                           "parent_manifest_sha256": prepare.sha(parent / "code_manifest.json"),
                           "parent_plan_sha256": prepare.sha(parent / "plan.json"),
                           "checkpoint": str(checkpoint),
                           "checkpoint_sha256": prepare.sha(checkpoint)}
            destination = {"code": str(target), "run": str(run)}
            preflight = execute(stage.remote_preflight_source(destination, fake_recipe))
            self.assertEqual(preflight["status"], "PASS_EXP236_TARGET_STAGE_PARENT_PREFLIGHT")
            staged = execute(stage.remote_stage_source(destination, fake_recipe, transfer, files))
            self.assertEqual(staged["status"], "STAGED_EXP236_TARGET44B6_CHUNK_NO_LABELS")
            self.assertIn("run_exp236_target_chunk.py",
                          (target / "exp227_job.py").read_text())
            self.assertEqual(staged["source_handoff_sha256"], runner.HANDOFF_SHA)
            self.assertEqual(staged["runner_sha256"], manifest["run_exp236_target_chunk.py"])
            local_plan = json.loads((target / "plan.json").read_text())
            local_plan.update(code=str(target), output=str(run / "output"),
                              checkpoint=str(checkpoint),
                              checkpoint_sha256=prepare.sha(checkpoint))
            (target / "plan.json").write_text(json.dumps(local_plan) + "\n")
            remote_manifest = json.loads((target / "code_manifest.json").read_text())
            remote_manifest["plan.json"] = prepare.sha(target / "plan.json")
            (target / "code_manifest.json").write_text(json.dumps(remote_manifest) + "\n")
            stage_record = {"manifest_sha256": prepare.sha(target / "code_manifest.json"),
                            "plan_sha256": prepare.sha(target / "plan.json"),
                            "source_handoff_sha256": runner.HANDOFF_SHA,
                            "checkpoint_sha256": prepare.sha(checkpoint),
                            "movies": plan["movies"]}
            config = {"code": str(target), "run": str(run), "chunk_index": 0,
                      "gpu": "GPU-test"}
            launched_preflight = execute(launch.preflight_source(stage_record, config))
            self.assertEqual(launched_preflight["status"],
                             "PASS_EXP236_TARGET_CHUNK_LAUNCH_PREFLIGHT")
            source = launch.launch_source(config, stage_record)
            output = io.StringIO()
            with patch("subprocess.check_output", return_value=""), \
                 patch("subprocess.Popen", side_effect=[SimpleNamespace(pid=101),
                                                         SimpleNamespace(pid=102)]), \
                 redirect_stdout(output):
                exec(compile(source, "<fake-launch>", "exec"), {})
            self.assertEqual(json.loads(output.getvalue()), {"wrapper": 101, "observe": 102})
            self.assertEqual(json.loads((run / "config.json").read_text()), config)


class FakeOps:
    def __init__(self, frozen):
        self.frozen = frozen
        self.calls = []
        self.active = None
        self.first_heartbeat = False
        self.foreign_waiting = False

    def prepare(self, index):
        self.calls.append(("prepare", index))
        return json.loads(prepare.paths(index)["receipt"].read_text())

    def stage(self, index):
        self.calls.append(("stage", index))
        p = self.prepare_record(index)
        return {"status": "STAGED_EXP236_TARGET44B6_CHUNK_NO_LABELS", "chunk_index": index,
                "code": p["code"], "run": p["run"], "lease_id": p["lease_id"],
                "manifest_sha256": "a" * 64, "plan_sha256": p["plan_sha256"],
                "source_handoff_sha256": runner.HANDOFF_SHA,
                "checkpoint_sha256": runner.CHECKPOINT_SHA, "movies": p["movies"],
                "remote_run_created": False, "gpu_claimed": False, "target_labels_read": False}

    def prepare_record(self, index):
        return json.loads(prepare.paths(index)["receipt"].read_text())

    def prelaunch_fair(self):
        index = next(i for i in range(4) if ("stage", i) in self.calls and
                     ("launch", i) not in self.calls)
        self.calls.append(("fair", index))
        requests = ([{"id": "foreign", "state": "WAITING_RESOURCE", "project": "other",
                      "gpus": []}] if self.foreign_waiting else [])
        return {"queue": {"requests": requests},
                "physical": {"all_gpus": ["GPU-idle"], "busy_gpus": [],
                             "idle_gpus": ["GPU-idle"]}}

    def launch(self, index):
        self.calls.append(("launch", index))
        self.active = index
        s = self.stage_record(index)
        return {**s, "status": "LAUNCHED_EXP236_TARGET44B6_CHUNK",
                "lease": {"id": s["lease_id"], "state": "RESERVED", "run_path": s["run"],
                          "alias": "nsu-a100", "owner": "biohub-agent",
                          "project": "biohub-cell-tracking-during-development", "pool": "a100",
                          "token": "sealed", "gpus": ["GPU-idle"]},
                "config": {"gpu": "GPU-idle", "token": "sealed", "pool": "a100",
                           "lease_id": s["lease_id"]},
                "fair_proof": {"physical_preclaim": {"all_gpus": ["GPU-idle"],
                                                       "busy_gpus": [], "idle_gpus": ["GPU-idle"]},
                               "queue_preclaim": [], "first_fair_idle_gpu": "GPU-idle"},
                "launch": {"wrapper": 1000 + index}, "control": {"controller_pid": 2000 + index}}

    def stage_record(self, index):
        p = self.prepare_record(index)
        return {"chunk_index": index, "code": p["code"], "run": p["run"],
                "manifest_sha256": "a" * 64, "plan_sha256": p["plan_sha256"],
                "lease_id": p["lease_id"], "target_labels_read": False}

    def completion(self, run):
        self.calls.append(("completion", self.active))
        if self.first_heartbeat:
            self.first_heartbeat = False
            return {"exit": None, "complete": None,
                    "control": {"action": "heartbeat",
                                "queue": {"state": "RUNNING", "run_path": run}}}
        exit_record = {"returncode": 0, "hard_timeout": False}
        return {"exit": exit_record,
                "complete": {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record},
                "control": {"action": "release",
                            "queue": {"state": "RELEASED", "run_path": run}}}

    def postrun(self, stage_record):
        index = self.active
        self.calls.append(("postrun", index))
        return {"status": "PASS_EXP236_TARGET44B6_CHUNK_POSTRUN_NO_LABELS",
                "chunk_index": index, "movies": self.frozen["chunks"][index],
                "graph_hashes": [{"dataset": name, "csv_sha256": "b" * 64,
                                  "receipt_sha256": "c" * 64}
                                 for name in self.frozen["chunks"][index]],
                "manifest_sha256": stage_record["manifest_sha256"],
                "plan_sha256": stage_record["plan_sha256"],
                "checkpoint_sha256": runner.CHECKPOINT_SHA,
                "status_sha256": "d" * 64, "exit_sha256": "e" * 64,
                "supervision_sha256": "f" * 64, "control_sha256": "1" * 64,
                "queue_state_in_control": "RELEASED", "target_labels_read": False}

    def queue_status(self):
        self.calls.append(("queue", self.active))
        s = self.stage_record(self.active)
        return {"requests": [{"id": s["lease_id"], "state": "RELEASED",
                              "run_path": s["run"], "owner": "biohub-agent",
                              "token": "sealed", "project": "biohub-cell-tracking-during-development",
                              "pool": "a100", "gpus": [],
                              "process": {"pid": 42 + self.active, "start": "123"}}]}

    def process_probe(self, config):
        self.calls.append(("probe", self.active))
        return {"exit": {"returncode": 0, "hard_timeout": False},
                "identity_alive": False, "group_alive": False, "gpu_pids": [],
                "launch": {"pid": 42 + self.active, "start": "123"}}


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.receipt = Path(self.tmp.name) / "coordinator.json"
        self.frozen = coord.frozen_inputs()
        self.ops = FakeOps(self.frozen)

    def run_coord(self, **kwargs):
        return coord.run(receipt=self.receipt, ops=self.ops, wait_seconds=0,
                         fair_wait_seconds=0, poll_seconds=60, **kwargs)

    def test_four_chunks_are_sequential_and_idempotent(self):
        state = self.run_coord()
        self.assertEqual(state["status"], "PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED")
        self.assertEqual(state["graph_count"], 59)
        self.assertFalse(state["target_labels_read"])
        self.assertEqual([call for call in self.ops.calls if call[0] == "launch"],
                         [("launch", i) for i in range(4)])
        saved = self.receipt.read_bytes()
        self.assertEqual(self.run_coord(), state)
        self.assertEqual(self.receipt.read_bytes(), saved)

    def test_heartbeat_waits_and_resume_does_not_duplicate_launch(self):
        self.ops.first_heartbeat = True
        waiting = self.run_coord()
        self.assertEqual(waiting["status"], "WAITING_FOR_RELEASE_NO_NEW_LAUNCH")
        self.assertNotIn(("launch", 1), self.ops.calls)
        final = self.run_coord(resume=True)
        self.assertEqual(final["graph_count"], 59)
        self.assertEqual(self.ops.calls.count(("launch", 0)), 1)

    def test_foreign_waiting_blocks_before_first_launch(self):
        self.ops.foreign_waiting = True
        waiting = self.run_coord()
        self.assertEqual(waiting["status"], "WAITING_FOR_FAIR_A100_NO_NEW_LAUNCH")
        self.assertNotIn(("launch", 0), self.ops.calls)


if __name__ == "__main__":
    unittest.main()
