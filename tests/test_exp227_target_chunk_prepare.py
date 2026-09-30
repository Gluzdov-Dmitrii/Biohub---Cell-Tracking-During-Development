"""Local-only source selection and target chunk00 safety contracts."""
import ast
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
import prepare_exp227_target_chunk0_local as prepare  # noqa: E402
import run_exp227_target_chunk as runner  # noqa: E402
import select_exp227_source_checkpoint as selector  # noqa: E402
import verify_exp227_target_chunk0 as postrun  # noqa: E402


def mock_selection():
    records = []
    for epoch, score in ((10, selector.EPOCH10_SCORE), (20, 0.82)):
        records.append({"epoch": epoch, "source_score": score,
                        "checkpoint": f"/remote/epoch_{epoch:03d}.pt",
                        "checkpoint_sha256": str(epoch // 10) * 64,
                        "graph_code": prepare.REMOTE + f"/code/exp227_source_graph{epoch}_v1_20260927",
                        "graph_manifest_sha256": str(epoch // 10 + 2) * 64})
    return {"status": "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT",
            "selected_epoch": 20, "scores": {"10": selector.EPOCH10_SCORE, "20": 0.82},
            "source8": list(selector.SOURCE8), "checkpoint": records[1]["checkpoint"],
            "checkpoint_sha256": records[1]["checkpoint_sha256"],
            "prereg_sha256": "a" * 64, "epochs": records,
            "remote_audit": {"status": "PASS_EXP227_SOURCE10_20_SELECTION_AUDIT",
                             "epochs": [{"epoch": 10}, {"epoch": 20}]},
            "target_labels_read": False}


class SourceSelectionTests(unittest.TestCase):
    def test_strict_source_only_selection_and_missing_score(self):
        self.assertEqual(selector.choose(selector.EPOCH10_SCORE, 0.82), 20)
        self.assertEqual(selector.choose(selector.EPOCH10_SCORE, selector.EPOCH10_SCORE), 10)
        self.assertEqual(selector.choose(selector.EPOCH10_SCORE, 0.80), 10)
        for bad in (float("nan"), float("inf"), None, True):
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                selector.choose(selector.EPOCH10_SCORE, bad)
        with self.assertRaises(AssertionError):
            selector.choose(0.81, 0.82)

    def test_actual_epoch10_receipts_bind_graph_and_official_scorer(self):
        evidence = selector.local_evidence(10)
        self.assertEqual(evidence["source_score"], selector.EPOCH10_SCORE)
        self.assertEqual(evidence["checkpoint_sha256"],
                         "df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79")
        self.assertEqual(evidence["evaluator_config_sha256"],
                         "45af14b5a6922324941a5f1d91052c373b1db7d7308a02cb6e9534ed47fce973")

    def test_remote_probe_is_read_only_and_parses(self):
        ast.parse(selector.REMOTE_PROBE.replace("ITEMS", "[]").replace("NAMES", "[]"))
        self.assertIn("gate['hashes']==hashes", selector.REMOTE_PROBE)
        self.assertIn("ctl['queue']['state']=='RELEASED'", selector.REMOTE_PROBE)
        self.assertIn("sex['returncode']==0", selector.REMOTE_PROBE)

    def test_real_source10_csv_sample_keeps_integer_graph_contract(self):
        # First five node rows from the sealed graph__44b6_996155de.csv;
        # full source CSV SHA256 ab4abc463eb91ae299eff5fa5a6031e45c5ffc54408cd7dc9613834d4b62b6b7.
        sample = (",".join(runner.COLUMNS) + "\n"
                  "0,44b6_996155de,node,2,0,0,24,4,-1,-1\n"
                  "1,44b6_996155de,node,9,0,0,105,20,-1,-1\n"
                  "2,44b6_996155de,node,10,0,0,120,93,-1,-1\n"
                  "3,44b6_996155de,node,11,0,0,171,140,-1,-1\n"
                  "4,44b6_996155de,node,14,0,2,124,16,-1,-1\n")
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "sample.csv"
            path.write_text(sample)
            row = {"dataset": "44b6_996155de", "shape": [100, 64, 256, 256]}
            self.assertEqual(runner.verify_csv(path, row), {"nodes": 5, "edges": 0})
            self.assertIn("v.is_integer()", selector.REMOTE_PROBE)
            self.assertIs(postrun.verify_csv, runner.verify_csv)
            path.write_text(sample.replace("0,0,24,4,-1,-1", "0,0,24.5,4,-1,-1", 1))
            with self.assertRaises((ValueError, AssertionError)):
                runner.verify_csv(path, row)


class TargetChunkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.assignment_bytes = prepare.ASSIGNMENT.read_bytes()
        self.assignment = json.loads(self.assignment_bytes)
        self.selection = mock_selection()
        self.selection_bytes = (json.dumps(self.selection, indent=2) + "\n").encode()

    def bundle(self):
        output = self.root / "bundle"
        result = prepare.build_bundle(self.selection, self.assignment, output,
                                      self.selection_bytes, self.assignment_bytes, "a" * 64)
        return output, result

    def test_local_bundle_exact_chunk_and_no_remote_mutation(self):
        output, result = self.bundle()
        self.assertEqual(len(result["plan"]["movies"]), 15)
        self.assertEqual(result["plan"]["movies"], self.assignment["directions"]["44b6"]["chunks"][0])
        self.assertEqual(result["recipe"]["status"], "LOCAL_ONLY_STAGE_RECIPE_NOT_EXECUTED")
        self.assertFalse((output / "code_manifest.json").exists())
        for name, digest in result["manifest"].items():
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
        self.assertEqual((output / "selection.json").read_bytes(), self.selection_bytes)
        self.assertEqual((output / "assignment.json").read_bytes(), self.assignment_bytes)
        self.assertIn("predict_one(", (output / "run_exp227_target_chunk.py").read_text())
        with self.assertRaises(FileExistsError):
            self.bundle()

    def test_runtime_plan_rejects_reassignment_and_checkpoint_choice(self):
        output, result = self.bundle()
        plan = result["plan"]
        local = dict(plan, assignment=str(output / "assignment.json"),
                     selection=str(output / "selection.json"))
        runner.validate_plan(local)
        with self.assertRaises(AssertionError):
            runner.validate_plan({**local, "movies": local["movies"][1:]})
        with self.assertRaises(AssertionError):
            runner.validate_plan({**local, "checkpoint_epoch": 10})
        with self.assertRaises(AssertionError):
            runner.validate_plan({**local, "checkpoint_sha256": "f" * 64})

    def test_later_chunk_keeps_same_checkpoint_and_frozen_membership(self):
        output = self.root / "bundle07"
        result = prepare.build_bundle(self.selection, self.assignment, output,
                                      self.selection_bytes, self.assignment_bytes,
                                      "a" * 64, chunk_index=7)
        plan = result["plan"]
        self.assertEqual(plan["chunk_index"], 7)
        self.assertEqual(plan["movies"], self.assignment["directions"]["44b6"]["chunks"][7])
        self.assertEqual(plan["checkpoint_sha256"], self.selection["checkpoint_sha256"])
        runner.validate_plan({**plan, "assignment": str(output / "assignment.json"),
                              "selection": str(output / "selection.json")})

    def test_geff_source_and_unassigned_images_denied(self):
        root = self.root / "images"
        guard = runner.no_labels_guard(root, self.assignment["directions"]["44b6"]["chunks"][0])
        good = root / (self.assignment["directions"]["44b6"]["chunks"][0][0] + ".zarr") / "0/zarr.json"
        guard("open", (good,))
        for bad in (root / "6bba_forbidden.zarr/0/zarr.json",
                    root / "44b6_source.zarr/0/zarr.json",
                    root / "6bba_forbidden.geff/attributes.json",
                    root / "frozen.csv",
                    self.root / "elsewhere/submission.csv",
                    self.root / "elsewhere/6bba_forbidden.geff/attributes.json"):
            with self.subTest(path=bad), self.assertRaises(PermissionError):
                guard("open", (bad,))

    def test_fair_a100_gate(self):
        lease = "exp227-target6bba-chunk00-v1-20260927"
        state = {"requests": [{"id": "other-running", "state": "RUNNING",
                               "project": "other", "gpus": ["GPU-A"]}]}
        self.assertEqual(prepare.fair_idle_a100(state, ["GPU-A", "GPU-B"], lease), "GPU-B")
        state["requests"].append({"id": "other-wait", "state": "WAITING_RESOURCE",
                                  "project": "other", "gpus": []})
        with self.assertRaisesRegex(AssertionError, "Foreign project"):
            prepare.fair_idle_a100(state, ["GPU-B"], lease)
        state["requests"].pop()
        with self.assertRaisesRegex(AssertionError, "No fair"):
            prepare.fair_idle_a100(state, ["GPU-A"], lease)
        state["requests"].append({"id": lease, "state": "RESERVED",
                                  "project": "biohub-cell-tracking-during-development", "gpus": ["GPU-B"]})
        with self.assertRaisesRegex(AssertionError, "Existing target lease"):
            prepare.fair_idle_a100(state, ["GPU-B"], lease)

    def test_selection_cannot_be_changed_by_target_metrics(self):
        self.selection["scores"]["20"] = 0.80
        with self.assertRaises(AssertionError):
            prepare.validate_selection(self.selection, "a" * 64)
        self.selection = mock_selection()
        self.selection["target_labels_read"] = True
        with self.assertRaises(AssertionError):
            prepare.validate_selection(self.selection, "a" * 64)

    def test_postrun_gate_checks_all_graphs_hashes_exit_and_release(self):
        bundle, built = self.bundle()
        code = self.root / "code/exp227_target6bba_chunk00_v1_20260927"
        run = self.root / "runs/exp227_target6bba_chunk00_v1_20260927"
        images = self.root / "data/exp213_source_view_20260912"
        code.mkdir(parents=True)
        output = run / "output"
        output.mkdir(parents=True)
        (run / "supervision").mkdir()
        for name in ("assignment.json", "selection.json", "run_exp227_target_chunk.py",
                     "run_exp223_inference.py", "verify_exp227_target_chunk0.py"):
            shutil.copy2(bundle / name, code / name)
        weight = self.root / "checkpoint.pt"
        weight.write_bytes(b"source-only mock")
        selected = json.loads((code / "selection.json").read_text())
        selected["checkpoint"] = str(weight)
        selected["checkpoint_sha256"] = postrun.sha(weight)
        selected["epochs"][1]["checkpoint"] = str(weight)
        selected["epochs"][1]["checkpoint_sha256"] = postrun.sha(weight)
        (code / "selection.json").write_text(json.dumps(selected))
        plan = dict(built["plan"], assignment=str(code / "assignment.json"),
                    selection=str(code / "selection.json"), checkpoint=str(weight),
                    selection_sha256=postrun.sha(code / "selection.json"),
                    checkpoint_sha256=postrun.sha(weight), data_root=images.as_posix(),
                    code=code.as_posix(), output=output.as_posix())
        (code / "plan.json").write_text(json.dumps(plan) + "\n")
        plan_sha = postrun.sha(code / "plan.json")
        (code / "code_manifest.json").write_text(json.dumps({
            p.name: postrun.sha(p) for p in code.iterdir() if p.is_file()}) + "\n")
        manifest_sha = postrun.sha(code / "code_manifest.json")
        records = []
        graph_text = (",".join(runner.COLUMNS) + "\n"
                      "0,DATASET,node,0,0,0,0,0,-1,-1\n"
                      "1,DATASET,node,1,1,0,0,0,-1,-1\n"
                      "2,DATASET,edge,-1,-1,-1,-1,-1,0,1\n")
        for name in plan["movies"]:
            zarr = images / (name + ".zarr")
            (zarr / "0").mkdir(parents=True)
            (zarr / "zarr.json").write_text("{}")
            (zarr / "0/zarr.json").write_text(json.dumps({"shape": [2, 2, 2, 2]}))
            csv_path = output / ("graph__" + name + ".csv")
            csv_path.write_text(graph_text.replace("DATASET", name))
            record = {"dataset": name, "csv": str(csv_path), "csv_sha256": postrun.sha(csv_path),
                      "checkpoint_sha256": plan["checkpoint_sha256"], "plan_sha256": plan_sha,
                      "shape": [2, 2, 2, 2], "nodes": 2, "edges": 1}
            csv_path.with_suffix(".json").write_text(json.dumps(record))
            records.append(record)
        status = {"status": "PASS_EXP227_TARGET6BBA_CHUNK00_NO_LABELS",
                  "target_labels_read": False, "source_embryo": "44b6", "target_embryo": "6bba",
                  "chunk_index": 0, "movies": plan["movies"], "assignment_sha256": plan["assignment_sha256"],
                  "selection_sha256": plan["selection_sha256"],
                  "checkpoint_sha256": plan["checkpoint_sha256"], "plan_sha256": plan_sha,
                  "records": records}
        (output / "status.json").write_text(json.dumps(status))
        exit_record = {"returncode": 0, "hard_timeout": False}
        (run / "exit.json").write_text(json.dumps(exit_record))
        (run / "supervision/complete.json").write_text(json.dumps({
            "status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record}))
        (run / "supervision/control.json").write_text(json.dumps({
            "action": "release", "queue": {"state": "RELEASED", "run_path": str(run)}}))
        result = postrun.gate(code, run, manifest_sha, plan_sha)
        self.assertEqual(len(result["graph_hashes"]), 15)
        queue = {"requests": [{"id": "chunk", "state": "RELEASED", "run_path": str(run)}]}
        self.assertEqual(postrun.live_release(queue, "chunk", run)["state"], "RELEASED")
        queue["requests"][0]["state"] = "RUNNING"
        with self.assertRaises(AssertionError):
            postrun.live_release(queue, "chunk", run)
        (output / ("graph__" + plan["movies"][0] + ".csv")).write_text("corrupt")
        with self.assertRaises(AssertionError):
            postrun.gate(code, run, manifest_sha, plan_sha)


if __name__ == "__main__":
    unittest.main()
