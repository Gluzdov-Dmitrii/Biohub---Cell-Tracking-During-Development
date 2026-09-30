"""Exact source44 Horaz continuation from epoch 10 through epoch 20."""
import argparse
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, sha256
from run_exp226_source_pilot import write_training_report


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PARENT_RUN = REMOTE + "/runs/exp227_horaz_source_block02_20260927"
RUN = REMOTE + "/runs/exp227_horaz_source_block03_20260927"
INITIAL_OUTPUT_ROOT = REMOTE + "/runs/exp227_horaz_source_block01_20260922/output"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"
PARENT_CHECKPOINT_SHA = "0c1ba0b73e91a5d19fc33ac5ba402f354f30c108e90c0626e49f8524201e3e55"
PARENT_RESULT_SHA = "9d95a2e91cd8ecdf7e599ec0bf22ed56358685cff5306369cf7a9b5aa22348e6"


def validate(plan):
    assert plan["experiment"] == "EXP227"
    assert plan["purpose"] == "source_only_full_training_block03"
    assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
    assert plan["fold"] == 1 and plan["seed"] == 3407
    assert plan["resume"] is True and plan["planned_epochs"] == 50
    assert (plan["start_epoch"], plan["block_end_epoch"]) == (11, 20)
    assert plan["parent_completed_epochs"] == 10
    assert plan["checkpoint_selection"] == "deferred_source_graph_10_20_30_40_50"
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert plan["parent_checkpoint_sha256"] == PARENT_CHECKPOINT_SHA
    assert plan["parent_result_sha256"] == PARENT_RESULT_SHA
    assert plan["parent_checkpoint"] == PARENT_RUN + "/output/fold1/last.pt"
    assert plan["initial_output_root"] == INITIAL_OUTPUT_ROOT
    assert plan["output"] == RUN + "/output"
    assert PurePosixPath(plan["data_root"]).is_absolute()
    assert len(plan["train"]) == 63 and len(plan["inner_validation"]) == 8
    rows = plan["train"] + plan["inner_validation"]
    names = [row["dataset_id"] for row in rows]
    assert len(names) == len(set(names)) == 71
    assert all(name.startswith("44b6_") for name in names)
    root = PurePosixPath(plan["data_root"])
    for row in rows:
        name = row["dataset_id"]
        assert row["zarr_path"] == str(root / (name + ".zarr"))
        assert row["geff_path"] == str(root / (name + ".geff"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    assert sha256(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    validate(plan)
    code = Path(__file__).resolve().parent
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve()) and sha256(path) == digest, name
    manifest_path = code / "source44_manifest.json"
    assert sha256(manifest_path) == SOURCE_MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    assert plan["train"] == manifest["train"]
    assert plan["inner_validation"] == manifest["inner_validation"]

    parent = Path(plan["parent_checkpoint"])
    parent_run = parent.parents[2]
    result_path = parent_run / "output/result.json"
    assert sha256(result_path) == PARENT_RESULT_SHA
    parent_result = json.loads(result_path.read_text())
    assert parent_result["status"] == "PASS_FULL_SOURCE_BLOCK_10_OF_50"
    assert parent_result["completed_epochs"] == 10
    assert parent_result["target_data_opened"] is False
    assert parent_result["checkpoint_reload"] == "PASS_weights_only"
    assert parent_result["checkpoint_sha256"] == PARENT_CHECKPOINT_SHA
    exit_record = json.loads((parent_run / "exit.json").read_text())
    supervision = json.loads((parent_run / "supervision/complete.json").read_text())
    control = json.loads((parent_run / "supervision/control.json").read_text())
    assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
    assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert supervision["exit"] == exit_record
    assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
    assert Path(control["queue"]["run_path"]).resolve() == parent_run.resolve()
    assert sha256(parent) == PARENT_CHECKPOINT_SHA
    history_path = parent.parent / "history.json"
    assert sha256(history_path) == plan["parent_history_sha256"]
    parent_history = json.loads(history_path.read_text())
    assert [row["epoch"] for row in parent_history] == list(range(1, 11))
    assert parent_result["history"] == parent_history

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    fold_dir = output / "fold1"
    fold_dir.mkdir()
    shutil.copy2(parent, fold_dir / "last.pt")
    assert sha256(fold_dir / "last.pt") == PARENT_CHECKPOINT_SHA
    (output / "contract.json").write_text(json.dumps(plan, indent=2) + "\n")
    sys.path.insert(0, str(code / "horaz/src/src"))
    guard = SourceAccessGuard(plan["train"] + plan["inner_validation"], output,
                              plan["data_root"])
    sys.addaudithook(guard)
    result = {"status": "RUNNING_EXP227_SOURCE_BLOCK03",
              "plan_sha256": args.plan_sha256,
              "parent_checkpoint_sha256": PARENT_CHECKPOINT_SHA,
              "parent_history_sha256": plan["parent_history_sha256"],
              "parent_result_sha256": PARENT_RESULT_SHA,
              "no_generalization_claim": True,
              "checkpoint_selection": plan["checkpoint_selection"]}
    started = time.time()
    try:
        import torch
        reporting = ModuleType("training_report")
        reporting.write_training_report = write_training_report
        sys.modules["training_report"] = reporting
        import train
        from engine import load_checkpoint

        assert torch.cuda.is_available()
        torch.set_num_threads(8)
        resolved = json.loads((code / "horaz/resolved_config.json").read_text())
        resolved.update(seed=3407, deterministic=False, epochs=50, num_workers=0,
                        torch_compile=False, max_iterations_per_epoch=None,
                        batch_size=4, max_frames=None,
                        output_root=INITIAL_OUTPUT_ROOT)
        checkpoint_meta = torch.load(fold_dir / "last.pt", map_location="cpu",
                                     weights_only=True)
        assert checkpoint_meta["epoch"] == 10
        assert checkpoint_meta["resolved_config"] == resolved
        assert checkpoint_meta["history"] == parent_history
        assert "optimizer" in checkpoint_meta and "rng_state" in checkpoint_meta
        del checkpoint_meta
        cfg = SimpleNamespace(**resolved)
        cfg.epochs = 20
        train.PERIODIC_EPOCHS = (20,)
        checkpoint = train.train_fold(cfg, 1, plan["train"],
                                      plan["inner_validation"], output, resolved,
                                      resume=True)
        history = json.loads((fold_dir / "history.json").read_text())
        assert [row["epoch"] for row in history] == list(range(1, 21))
        assert history[:10] == parent_history
        assert all(row["training_iterations"] > 8 for row in history[10:])
        assert all(math.isfinite(value) for row in history for value in row.values()
                   if isinstance(value, (int, float)))
        assert Path(checkpoint).resolve() == (fold_dir / "last.pt").resolve()
        final_meta = torch.load(checkpoint, map_location="cpu", weights_only=True)
        assert final_meta["epoch"] == 20
        assert final_meta["resolved_config"] == resolved
        assert final_meta["history"] == history
        assert "optimizer" in final_meta and "rng_state" in final_meta
        del final_meta
        model, _ = load_checkpoint(checkpoint, torch.device("cpu"))
        assert all(torch.isfinite(value).all().item() for value in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        periodic = fold_dir / "epoch_020.pt"
        assert periodic.is_file()
        result.update(status="PASS_FULL_SOURCE_BLOCK_20_OF_50",
                      elapsed_seconds=time.time() - started,
                      checkpoint_sha256=sha256(checkpoint),
                      periodic_checkpoint_sha256=sha256(periodic),
                      checkpoint_reload="PASS_weights_only",
                      completed_epochs=20, planned_epochs=50,
                      history=history)
    except BaseException as exc:
        result.update(status="FAILED_EXP227_SOURCE_BLOCK03", error=repr(exc),
                      elapsed_seconds=time.time() - started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids),
                      denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else "attempt_blocked")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({key: value for key, value in result.items()
                          if key != "history"}), flush=True)


if __name__ == "__main__":
    main()
