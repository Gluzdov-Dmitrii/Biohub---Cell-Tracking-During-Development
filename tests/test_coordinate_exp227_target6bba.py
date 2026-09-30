"""Local-only tests of the finite EXP227 target6bba coordinator."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import coordinate_exp227_target6bba as coordinator  # noqa: E402
import prepare_exp227_target_chunk0_local as prepare  # noqa: E402
import stage_exp227_target_chunk as stager  # noqa: E402


def frozen():
    assignment = json.loads(coordinator.ASSIGNMENT.read_text())
    chunks = assignment["directions"]["44b6"]["chunks"]
    assert len(chunks) == 8 and sum(map(len, chunks)) == 116
    return {"assignment_sha256": coordinator.ASSIGNMENT_SHA, "prereg_sha256": "a" * 64,
            "selection_sha256": "b" * 64, "checkpoint_sha256": "c" * 64,
            "selected_epoch": 20, "chunks": chunks}


class FakeOps:
    def __init__(self, fixed):
        self.fixed = fixed
        self.calls = []
        self.pending = False
        self.bad_graph_index = None
        self.bad_queue_index = None
        self.fail_launch_index = None
        self.active_index = None
        self.no_gpu = False
        self.foreign_waiting = False

    def prepare(self, index):
        self.calls.append(("prepare", index))
        return {"status": "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY", "chunk_index": index,
                "movies": self.fixed["chunks"][index], "bundle": str(ROOT / "scripts"),
                "plan_sha256": str(index + 1) * 64,
                "assignment_sha256": self.fixed["assignment_sha256"],
                "prereg_sha256": self.fixed["prereg_sha256"],
                "selected_epoch": self.fixed["selected_epoch"],
                "selection_sha256": self.fixed["selection_sha256"],
                "checkpoint_sha256": self.fixed["checkpoint_sha256"],
                "lease_id": "exp227-target-" + str(index),
                "remote_stage_created": False, "remote_run_created": False,
                "gpu_claimed": False,
                "target_labels_read": False}

    def stage(self, index):
        self.calls.append(("stage", index))
        suffix = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
        return {"status": "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS", "chunk_index": index,
                "code": coordinator.RUN_PREFIX + "/code/" + suffix,
                "run": coordinator.RUN_PREFIX + "/runs/" + suffix,
                "manifest_sha256": "d" * 64, "plan_sha256": str(index + 1) * 64,
                "lease_id": "exp227-target-" + str(index),
                "movies": self.fixed["chunks"][index],
                "selection_sha256": self.fixed["selection_sha256"],
                "checkpoint_sha256": self.fixed["checkpoint_sha256"],
                "remote_run_created": False, "gpu_claimed": False,
                "target_labels_read": False}

    def launch(self, index):
        self.calls.append(("launch", index))
        self.active_index = index
        if index == self.fail_launch_index:
            raise RuntimeError("Uncertain launch state")
        result = self.stage_record(index)
        result.update(status="LAUNCHED_EXP227_TARGET6BBA_CHUNK",
                      lease={"id": result["lease_id"], "state": "RESERVED",
                             "run_path": result["run"], "alias": "nsu-a100", "owner": "biohub-agent",
                             "project": "biohub-cell-tracking-during-development",
                             "token": "sealed", "gpus": ["GPU-idle"]},
                      config={"gpu": "GPU-idle", "token": "sealed", "pool": "a100",
                              "lease_id": result["lease_id"]},
                      fair_proof={"physical_preclaim": {"all_gpus": ["GPU-idle"],
                                                         "busy_gpus": [], "idle_gpus": ["GPU-idle"]},
                                  "queue_preclaim": [], "first_fair_idle_gpu": "GPU-idle"},
                      launch={"pid": 1000 + index}, control={"controller_pid": 2000 + index})
        return result

    def stage_record(self, index):
        suffix = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
        return {"chunk_index": index, "code": coordinator.RUN_PREFIX + "/code/" + suffix,
                "run": coordinator.RUN_PREFIX + "/runs/" + suffix,
                "manifest_sha256": "d" * 64, "plan_sha256": str(index + 1) * 64,
                "lease_id": "exp227-target-" + str(index), "target_labels_read": False}

    def completion(self, run):
        self.calls.append(("completion", self.active_index))
        if self.pending:
            return {"exit": None, "complete": None, "control": None}
        exit_record = {"returncode": 0, "hard_timeout": False}
        return {"exit": exit_record,
                "complete": {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record},
                "control": {"action": "release", "queue": {"state": "RELEASED", "run_path": run}}}

    def prelaunch_fair(self):
        index = next(i for i in range(8) if ("stage", i) in self.calls and
                     ("launch", i) not in self.calls)
        self.calls.append(("fair", index))
        requests = ([{"id": "foreign-first", "state": "WAITING_RESOURCE",
                      "project": "other", "gpus": []}] if self.foreign_waiting else [])
        return {"queue": {"requests": requests},
                "physical": {"all_gpus": ["GPU-idle"],
                             "busy_gpus": ["GPU-idle"] if self.no_gpu else [],
                             "idle_gpus": [] if self.no_gpu else ["GPU-idle"]}}

    def postrun(self, stage):
        index = self.active_index
        self.calls.append(("postrun", index))
        hashes = [{"dataset": name, "csv_sha256": "e" * 64,
                   "receipt_sha256": "f" * 64} for name in self.fixed["chunks"][index]]
        if self.bad_graph_index == index:
            hashes[0]["csv_sha256"] = "bad"
        return {"status": "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS",
                "chunk_index": index, "movies": self.fixed["chunks"][index],
                "graph_hashes": hashes, "manifest_sha256": stage["manifest_sha256"],
                "plan_sha256": stage["plan_sha256"],
                "checkpoint_sha256": self.fixed["checkpoint_sha256"],
                "status_sha256": "1" * 64, "exit_sha256": "2" * 64,
                "supervision_sha256": "3" * 64, "control_sha256": "4" * 64,
                "queue_state_in_control": "RELEASED", "target_labels_read": False}

    def queue_status(self):
        index = self.active_index
        self.calls.append(("queue", index))
        suffix = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
        return {"requests": [{"id": "exp227-target-" + str(index),
                              "state": "RUNNING" if index == self.bad_queue_index else "RELEASED",
                              "run_path": coordinator.RUN_PREFIX + "/runs/" + suffix}]}


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "coordinator.json"
        self.fixed = frozen()
        self.ops = FakeOps(self.fixed)
        self.patch = patch.object(coordinator, "frozen_inputs", return_value=self.fixed)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_coordinator(self, **kwargs):
        return coordinator.run(receipt=self.path, ops=self.ops, wait_seconds=0,
                               fair_wait_seconds=0, poll_seconds=60, **kwargs)

    def test_frozen_assignment_is_exact_116_in_eight_ordered_chunks(self):
        self.assertEqual(coordinator.sha(coordinator.ASSIGNMENT), coordinator.ASSIGNMENT_SHA)
        self.assertEqual([len(chunk) for chunk in self.fixed["chunks"]], [15] * 4 + [14] * 4)
        names = [name for chunk in self.fixed["chunks"] for name in chunk]
        self.assertEqual(len(set(names)), 116)

    def test_all_eight_are_sequential_and_final_receipt_is_idempotent(self):
        state = self.run_coordinator()
        self.assertEqual(state["status"], "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED")
        self.assertEqual(state["graph_count"], 116)
        self.assertTrue(state["all_leases_released"])
        self.assertFalse(state["target_labels_read"])
        self.assertFalse(state["target_score_computed"])
        expected = [(kind, index) for index in range(8)
                    for kind in ("prepare", "stage", "fair", "launch", "completion", "postrun", "queue")]
        self.assertEqual(self.ops.calls, expected)
        saved = self.path.read_bytes()
        self.assertEqual(self.run_coordinator(), state)
        self.assertEqual(self.path.read_bytes(), saved)
        self.assertEqual(self.ops.calls, expected)

    def test_pending_run_resumes_wait_only_without_second_launch(self):
        self.ops.pending = True
        first = self.run_coordinator()
        self.assertEqual(first["status"], "WAITING_FOR_RELEASE_NO_NEW_LAUNCH")
        self.assertEqual(first["waiting_chunk_index"], 0)
        self.assertEqual([call for call in self.ops.calls if call[0] == "launch"], [("launch", 0)])
        self.ops.pending = False
        completed = self.run_coordinator(resume=True)
        self.assertEqual(completed["graph_count"], 116)
        self.assertEqual([call for call in self.ops.calls if call == ("launch", 0)], [("launch", 0)])

    def test_in_progress_heartbeat_waits_without_stopping_or_relaunching(self):
        completed = self.ops.completion
        first = [True]

        def heartbeat_then_release(run):
            if first[0]:
                first[0] = False
                self.ops.calls.append(("completion", self.ops.active_index))
                return {"exit": None, "complete": None,
                        "control": {"action": "heartbeat",
                                    "queue": {"state": "RUNNING", "run_path": run}}}
            return completed(run)

        self.ops.completion = heartbeat_then_release
        waiting = self.run_coordinator()
        self.assertEqual(waiting["status"], "WAITING_FOR_RELEASE_NO_NEW_LAUNCH")
        self.assertNotIn(("postrun", 0), self.ops.calls)
        self.assertNotIn(("prepare", 1), self.ops.calls)
        final = self.run_coordinator(resume=True)
        self.assertEqual(final["graph_count"], 116)
        self.assertEqual([call for call in self.ops.calls if call == ("launch", 0)],
                         [("launch", 0)])

    def test_completion_still_rejects_false_release_and_completion(self):
        run = "/exact/run"
        heartbeat = {"action": "heartbeat", "queue": {"state": "RUNNING", "run_path": run}}
        self.assertFalse(coordinator._completion_ready(
            {"exit": {"returncode": 0, "hard_timeout": False},
             "complete": None, "control": heartbeat}, run))
        with self.assertRaisesRegex(ValueError, "Bad queue control heartbeat"):
            coordinator._completion_ready(
                {"exit": {"returncode": 0, "hard_timeout": False},
                 "complete": {"status": "RELEASED_AFTER_VERIFIED_EXIT",
                              "exit": {"returncode": 0, "hard_timeout": False}},
                 "control": heartbeat}, run)
        with self.assertRaisesRegex(ValueError, "Bad queue control release"):
            coordinator._completion_ready(
                {"exit": {"returncode": 0, "hard_timeout": False},
                 "complete": None,
                 "control": {"action": "release",
                             "queue": {"state": "RUNNING", "run_path": run}}}, run)

    def test_no_idle_gpu_waits_before_launch_then_resumes_without_restage(self):
        self.ops.no_gpu = True
        first = self.run_coordinator()
        self.assertEqual(first["status"], "WAITING_FOR_FAIR_A100_NO_NEW_LAUNCH")
        self.assertEqual(first["wait_reason"], "NO_FAIR_IDLE_A100")
        self.assertNotIn(("launch", 0), self.ops.calls)
        self.ops.no_gpu = False
        final = self.run_coordinator(resume=True)
        self.assertEqual(final["graph_count"], 116)
        self.assertEqual([call for call in self.ops.calls if call == ("prepare", 0)],
                         [("prepare", 0)])
        self.assertEqual([call for call in self.ops.calls if call == ("stage", 0)],
                         [("stage", 0)])
        self.assertEqual([call for call in self.ops.calls if call == ("launch", 0)],
                         [("launch", 0)])

    def test_foreign_waiting_defers_launch_and_resumes_after_queue_clears(self):
        self.ops.foreign_waiting = True
        first = self.run_coordinator()
        self.assertEqual(first["status"], "WAITING_FOR_FAIR_A100_NO_NEW_LAUNCH")
        self.assertEqual(first["wait_reason"], "FOREIGN_WAITING")
        self.assertNotIn(("launch", 0), self.ops.calls)
        self.ops.foreign_waiting = False
        final = self.run_coordinator(resume=True)
        self.assertEqual(final["graph_count"], 116)
        self.assertEqual([call for call in self.ops.calls if call == ("stage", 0)],
                         [("stage", 0)])

    def test_fair_wait_uses_bounded_sixty_second_or_longer_polling(self):
        self.ops.no_gpu = True
        now = [0.0]
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds

        state = coordinator.run(receipt=self.path, ops=self.ops, wait_seconds=0,
                                fair_wait_seconds=120, poll_seconds=60,
                                sleeper=sleep, monotonic=lambda: now[0])
        self.assertEqual(state["status"], "WAITING_FOR_FAIR_A100_NO_NEW_LAUNCH")
        self.assertEqual(sleeps, [60, 60])
        self.assertEqual([call for call in self.ops.calls if call == ("fair", 0)],
                         [("fair", 0)] * 3)
        self.assertNotIn(("launch", 0), self.ops.calls)

    def test_launch_exception_leaves_intent_and_blocks_blind_retry(self):
        self.ops.fail_launch_index = 0
        with self.assertRaisesRegex(RuntimeError, "Uncertain launch"):
            self.run_coordinator()
        state = coordinator._read_state(self.path)
        self.assertEqual(state["status"], "STOPPED_NEEDS_RECONCILIATION")
        self.assertIn("intent_unix", state["chunks"][0]["launch"])
        self.assertNotIn("result", state["chunks"][0]["launch"])
        with self.assertRaises(coordinator.ReconciliationNeeded):
            self.run_coordinator(resume=True)
        self.assertEqual([call for call in self.ops.calls if call[0] == "launch"], [("launch", 0)])

    def test_first_graph_hash_anomaly_stops_before_chunk_one(self):
        self.ops.bad_graph_index = 0
        with self.assertRaisesRegex(ValueError, "graph hash"):
            self.run_coordinator()
        self.assertEqual(self.ops.calls[-1], ("postrun", 0))
        self.assertNotIn(("prepare", 1), self.ops.calls)
        self.assertEqual(coordinator._read_state(self.path)["status"],
                         "STOPPED_NEEDS_RECONCILIATION")

    def test_live_queue_release_anomaly_stops_before_chunk_one(self):
        self.ops.bad_queue_index = 0
        with self.assertRaises(AssertionError):
            self.run_coordinator()
        self.assertEqual(self.ops.calls[-1], ("queue", 0))
        self.assertNotIn(("prepare", 1), self.ops.calls)

    def test_changed_frozen_inputs_and_receipt_corruption_block_resume(self):
        self.ops.pending = True
        self.run_coordinator()
        changed = dict(self.fixed, checkpoint_sha256="9" * 64)
        with patch.object(coordinator, "frozen_inputs", return_value=changed):
            with self.assertRaisesRegex(ValueError, "Frozen inputs differ"):
                self.run_coordinator(resume=True)
        state = json.loads(self.path.read_text())
        state["chunks"][0]["stage"]["result"]["lease_id"] = "tampered"
        self.path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            self.run_coordinator(resume=True)

    def test_bad_completion_exit_stops_without_graph_or_next_chunk(self):
        def failed_completion(run):
            self.ops.calls.append(("completion", self.ops.active_index))
            return {"exit": {"returncode": 1, "hard_timeout": False},
                    "complete": None, "control": None}
        self.ops.completion = failed_completion
        with self.assertRaisesRegex(ValueError, "failed or timed out"):
            self.run_coordinator()
        self.assertNotIn(("postrun", 0), self.ops.calls)
        self.assertNotIn(("prepare", 1), self.ops.calls)

    def test_foreign_waiting_preclaim_rejects_launch_receipt(self):
        original = self.ops.launch

        def unfair(index):
            result = original(index)
            result["fair_proof"]["queue_preclaim"] = [{
                "id": "foreign-first", "state": "WAITING_RESOURCE", "project": "other",
                "gpus": [], "run_path": "/other"}]
            return result

        self.ops.launch = unfair
        with self.assertRaisesRegex(ValueError, "foreign WAITING"):
            self.run_coordinator()
        self.assertNotIn(("completion", 0), self.ops.calls)
        self.assertNotIn(("prepare", 1), self.ops.calls)

    def test_existing_coordinator_lock_blocks_all_side_effects(self):
        lock = self.path.with_name(self.path.name + ".lock")
        lock.write_text("other coordinator")
        with self.assertRaisesRegex(coordinator.ReconciliationNeeded, "lock exists"):
            self.run_coordinator()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.ops.calls, [])

    def test_existing_local_prepare_is_read_only_audited_not_rebuilt(self):
        bundle = self.path.parent / "bundle"
        bundle.mkdir()
        prepared_file = self.path.parent / "prepare.json"
        prepared_file.write_text("{}")
        with patch("prepare_exp227_target_chunk0_local.paths",
                   return_value={"bundle": bundle, "receipt": prepared_file}), \
             patch("stage_exp227_target_chunk.local_gate",
                   return_value=({"status": "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY"},)) as gate, \
             patch("prepare_exp227_target_chunk0_local.prepare_index",
                   side_effect=AssertionError("builder was called")):
            result = coordinator.DefaultOps().prepare(0)
        self.assertEqual(result["status"], "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY")
        gate.assert_called_once_with(0)

    def test_actual_chunk_zero_prepare_is_reused_without_mutation(self):
        paths = prepare.paths(0)
        if not paths["bundle"].is_dir() or not paths["receipt"].is_file():
            self.skipTest("Actual chunk00 local preparation is not present")
        if stager.stage_paths(0)["stage"].exists():
            self.skipTest("Actual chunk00 has already been staged")
        before = {path.name: coordinator.sha(path) for path in paths["bundle"].iterdir()
                  if path.is_file()}
        receipt_before = paths["receipt"].read_bytes()
        with patch.object(prepare, "prepare_index", side_effect=AssertionError("builder was called")):
            result = coordinator.DefaultOps().prepare(0)
        self.assertEqual(result, json.loads(receipt_before))
        self.assertEqual(result["selected_epoch"], 10)
        self.assertEqual(receipt_before, paths["receipt"].read_bytes())
        self.assertEqual(before, {path.name: coordinator.sha(path)
                                  for path in paths["bundle"].iterdir() if path.is_file()})


if __name__ == "__main__":
    unittest.main()
