"""Local-only tests for the separate EXP227 chunk00 recovery receipt."""
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import coordinate_exp227_target6bba as coord  # noqa: E402
import recover_exp227_target6bba_chunk00 as recovery  # noqa: E402


class FakeRemote:
    def __init__(self, state, stage, launch):
        self.stage = stage
        self.launch = launch
        self.exit = {"returncode": 0, "hard_timeout": False}
        self.process = {"pid": 42, "start": "123"}
        self.row = {**launch["lease"], "state": "RELEASED", "gpus": [],
                    "process": self.process}
        self.gate = {"status": "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS",
                     "chunk_index": 0, "movies": state["frozen"]["chunks"][0],
                     "graph_hashes": [{"dataset": movie, "csv_sha256": "a" * 64,
                                       "receipt_sha256": "b" * 64}
                                      for movie in state["frozen"]["chunks"][0]],
                     "manifest_sha256": stage["manifest_sha256"],
                     "plan_sha256": stage["plan_sha256"],
                     "checkpoint_sha256": stage["checkpoint_sha256"],
                     "status_sha256": "c" * 64, "exit_sha256": "d" * 64,
                     "supervision_sha256": "e" * 64, "control_sha256": "f" * 64,
                     "queue_state_in_control": "RELEASED", "target_labels_read": False}

    def completion(self, run):
        assert run == self.stage["run"]
        return {"exit": self.exit,
                "complete": {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": self.exit},
                "control": {"action": "release", "queue": self.row}}

    def postrun(self, stage):
        assert stage == self.stage
        return self.gate

    def queue_status(self):
        return {"requests": [self.row]}

    def probe(self, config):
        assert config == self.launch["config"]
        return {"exit": self.exit, "identity_alive": False, "group_alive": False,
                "gpu_pids": [], "launch": {**self.process, "command": ["python3"]},
                "status": {"status": "PASS_EXP227_TARGET6BBA_CHUNK00_NO_LABELS"}}


class RecoveryTests(unittest.TestCase):
    def test_read_only_gate_and_separate_receipt_preserve_stopped_source(self):
        state, _, stage, launch = recovery.stopped_state()
        remote = FakeRemote(state, stage, launch)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "stopped.json"
            successor = Path(directory) / "recovered.json"
            source.write_bytes(recovery.SOURCE.read_bytes())
            before = source.read_bytes()
            _, evidence, postrun = recovery.audit(source=source, ops=remote,
                                                   process_probe=remote.probe)
            self.assertEqual(evidence["movie_count"], 15)
            self.assertEqual(evidence["queue_state"], "RELEASED")
            self.assertFalse(successor.exists())
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue(postrun["validated"])
            output = recovery.write_recovered(source=source, recovered=successor,
                                              ops=remote, process_probe=remote.probe)
            self.assertEqual(output["recovered_receipt_sha256"], coord.sha(successor))
            self.assertEqual(source.read_bytes(), before)
            recovered = coord._read_state(successor)
            self.assertEqual(recovered["status"], "ACTIVE_NO_TARGET_LABELS")
            self.assertTrue(recovered["chunks"][0]["postrun"]["validated"])
            self.assertEqual(recovered["chunks"][1], {})
            self.assertNotIn("error", recovered)
            with self.assertRaisesRegex(ValueError, "already exists"):
                recovery.write_recovered(source=source, recovered=successor,
                                         ops=remote, process_probe=remote.probe)

    def test_bad_live_process_blocks_recovery(self):
        state, _, stage, launch = recovery.stopped_state()
        remote = FakeRemote(state, stage, launch)
        def live_group(config):
            result = remote.probe(config)
            result["group_alive"] = True
            return result
        with self.assertRaisesRegex(ValueError, "still active"):
            recovery.audit(ops=remote, process_probe=live_group)


if __name__ == "__main__":
    unittest.main()
