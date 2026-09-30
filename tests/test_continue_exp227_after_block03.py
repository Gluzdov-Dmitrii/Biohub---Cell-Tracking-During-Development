"""Finite, fail-closed source20 handoff contracts without remote activity."""
import ast
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import continue_exp227_after_block03 as handoff  # noqa: E402


def training_observation():
    return {"exit": {"returncode": 0, "hard_timeout": False},
            "result_status": "PASS_FULL_SOURCE_BLOCK_20_OF_50",
            "completed_epochs": 20, "epochs": 20, "last_epoch": 20,
            "target_data_opened": False, "checkpoint20_exists": True,
            "complete_status": "RELEASED_AFTER_VERIFIED_EXIT", "control_state": "RELEASED"}


def graph_observation():
    names = list(handoff.INNER_IDS)
    return {"exit": {"returncode": 0, "hard_timeout": False},
            "status": "PASS_EXP227_SOURCE_GRAPH20_NO_LABELS",
            "source_labels_read": False, "target_labels_read": False,
            "movies": names, "records": 8,
            "complete_status": "RELEASED_AFTER_VERIFIED_EXIT", "control_state": "RELEASED",
            "output_names": ["status.json"] +
            ["graph__" + name + suffix for name in names for suffix in (".csv", ".json")]}


class HandoffContract(unittest.TestCase):
    def test_training_requires_success_and_release(self):
        lease = {"state": "RELEASED"}
        self.assertTrue(handoff.check_training(lease, training_observation()))
        self.assertFalse(handoff.check_training({"state": "RUNNING"}, training_observation()))
        for change in ({"exit": {"returncode": 1, "hard_timeout": False}},
                       {"result_status": "FAILED_EXP227_SOURCE_BLOCK03"},
                       {"target_data_opened": True}, {"checkpoint20_exists": False}):
            with self.subTest(change=change), self.assertRaises((AssertionError, RuntimeError)):
                handoff.check_training(lease, {**training_observation(), **change})

    def test_graph_requires_all_eight_no_label_outputs(self):
        lease = {"state": "RELEASED"}
        self.assertTrue(handoff.check_graph(lease, graph_observation()))
        for change in ({"source_labels_read": True}, {"target_labels_read": True},
                       {"movies": list(handoff.INNER_IDS[:-1])},
                       {"output_names": ["status.json"]}):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                handoff.check_graph(lease, {**graph_observation(), **change})

    def test_score_requires_finite_success(self):
        good = {"exit": {"returncode": 0, "timeout": False},
                "result_status": "PASS_EXP227_SOURCE_GRAPH20_OFFICIAL",
                "rows": 8, "source_score": 0.82}
        self.assertTrue(handoff.check_score(good))
        self.assertFalse(handoff.check_score({**good, "exit": None, "result_status": None}))
        for change in ({"exit": {"returncode": 1, "timeout": False}},
                       {"exit": {"returncode": 0, "timeout": True}},
                       {"rows": 7}, {"source_score": float("nan")}):
            with self.subTest(change=change), self.assertRaises((AssertionError, RuntimeError)):
                handoff.check_score({**good, **change})

    def test_probe_templates_parse(self):
        scripts = []

        def fake_ssh(alias, command, source=None):
            ast.parse(source)
            scripts.append(source)
            return {}

        with patch.object(handoff, "ssh", fake_ssh):
            handoff.probe_gpu_run(handoff.TRAIN_RUN, "nsu-a100")
            handoff.probe_gpu_run(handoff.GRAPH_RUN, "nsu-a100")
            handoff.probe_score()
        self.assertEqual(len(scripts), 3)
        self.assertIn("checkpoint20_exists", scripts[0])
        self.assertIn("source_labels_read", scripts[1])
        self.assertIn("result_status", scripts[2])

    def test_main_stops_at_verified_source_score(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = root / "handoff.json"
            paths = {
                "RECEIPT": receipt,
                "GRAPH_CONFIG": root / "graph_config.json",
                "GRAPH_PREPARED": root / "graph_prepare.json",
                "GRAPH_LAUNCHED": root / "graph_launch.json",
                "SCORE_PREPARED": root / "score_prepare.json",
                "SCORE_LAUNCHED": root / "score_launch.json",
                "SCORE_VERIFIED": root / "score_verified.json",
            }
            steps = []

            def fake_wait(name, seconds, interval, probe, check, result):
                steps.append("wait_" + name)
                return {}

            def fake_step(name, script, result):
                steps.append(name)
                for key in ({"prepare_graph": ("GRAPH_CONFIG", "GRAPH_PREPARED"),
                             "launch_graph": ("GRAPH_LAUNCHED",),
                             "prepare_score": ("SCORE_PREPARED",),
                             "launch_score": ("SCORE_LAUNCHED",),
                             "verify_score": ("SCORE_VERIFIED",)}[name]):
                    value = ({"status": "VERIFIED_EXP227_SOURCE20_OFFICIAL",
                              "source_labels_read": True, "target_labels_read": False}
                             if key == "SCORE_VERIFIED" else {})
                    paths[key].write_text(json.dumps(value))

            with ExitStack() as stack:
                for key, path in paths.items():
                    stack.enter_context(patch.object(handoff, key, path))
                stack.enter_context(patch.object(handoff, "wait_for", fake_wait))
                stack.enter_context(patch.object(handoff, "run_step", fake_step))
                handoff.main()
            self.assertEqual(steps, ["wait_training", "prepare_graph", "launch_graph",
                                     "wait_graph", "prepare_score", "launch_score",
                                     "wait_score", "verify_score"])
            self.assertEqual(json.loads(receipt.read_text())["status"],
                             "PASS_EXP227_SOURCE20_OFFICIAL_HANDOFF")

    def test_existing_handoff_cannot_restart(self):
        with tempfile.TemporaryDirectory() as name:
            receipt = Path(name) / "handoff.json"
            receipt.write_text("{}")
            with patch.object(handoff, "RECEIPT", receipt), self.assertRaises(AssertionError):
                handoff.main()


if __name__ == "__main__":
    unittest.main()
