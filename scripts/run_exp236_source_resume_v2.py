"""Exact v2 source6bba continuation with the frozen duplicate-window filter."""
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


SOURCE_MANIFEST_SHA = "a5c3176ec25d4d75321e6c1fe17b62be2d9e25472ae7fcb677e48fe71478bd87"
SOURCE_BUNDLE_SHA = "90e95a45a4d58a72c18495b48c979de52afdc080b9070892c53e8bf41c2f59b1"
SOURCE_DUPLICATE_MAP_SHA = "d73389f47cc7cbf1c50a01a788827119aa324eebf2fb9222a66243b168ca7d62"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
INITIAL_OUTPUT_ROOT = REMOTE + "/runs/exp236_horaz_source6bba_block01_v2_20260927/output"
STEPS = {(4, 6), (7, 9), (10, 10)}


def validate(plan):
    assert plan["experiment"] == "EXP236"
    assert plan["purpose"] == "source_only_reciprocal_horaz_resume"
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    assert plan["fold"] == 0 and plan["resume"] is True
    assert plan["planned_epochs"] == 50
    assert (plan["start_epoch"], plan["block_end_epoch"]) in STEPS
    assert plan["parent_completed_epochs"] == plan["start_epoch"] - 1
    assert plan["checkpoint_selection"] == "deferred_source_graph_10_20_30_40_50"
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert plan["source_duplicate_policy"] == "exclude_all_effective_duplicate_windows_v2"
    assert plan["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert plan["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert plan["removed_sampled_windows_by_split"] == {"train": 809,
                                                         "inner_validation": 101}
    assert plan["initial_output_root"] == INITIAL_OUTPUT_ROOT
    parent_block = {3: 1, 6: 2, 9: 3}[plan["parent_completed_epochs"]]
    next_block = parent_block + 1
    parent_stem = f"exp236_horaz_source6bba_block{parent_block:02d}_v2_20260927"
    next_stem = f"exp236_horaz_source6bba_block{next_block:02d}_v2_20260927"
    assert plan["parent_code"] == REMOTE + "/code/" + parent_stem
    assert plan["parent_checkpoint"] == REMOTE + "/runs/" + parent_stem + "/output/fold0/last.pt"
    assert plan["output"] == REMOTE + "/runs/" + next_stem + "/output"
    assert len(plan["parent_plan_sha256"]) == len(plan["parent_code_manifest_sha256"]) == 64
    assert len(plan["train"]) == 115 and len(plan["inner_validation"]) == 11
    names = [row["dataset_id"] for row in plan["train"] + plan["inner_validation"]]
    assert len(names) == len(set(names)) == 126
    assert all(name.startswith("6bba_") for name in names)
    data_root = PurePosixPath(plan["data_root"])
    for row in plan["train"] + plan["inner_validation"]:
        name = row["dataset_id"]
        assert row["zarr_path"] == str(data_root / (name + ".zarr"))
        assert row["geff_path"] == str(data_root / (name + ".geff"))


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
        assert sha256(code / name) == digest, name
    manifest_path = code / "source6bba_manifest.json"
    assert sha256(manifest_path) == SOURCE_MANIFEST_SHA
    duplicate_map_path = code / "horaz/src/src/exp236_source_duplicate_pairs.json"
    assert sha256(duplicate_map_path) == SOURCE_DUPLICATE_MAP_SHA
    manifest = json.loads(manifest_path.read_text())
    assert plan["train"] == manifest["train"]
    assert plan["inner_validation"] == manifest["inner_validation"]

    parent = Path(plan["parent_checkpoint"])
    parent_run = parent.parents[2]
    parent_code = Path(plan["parent_code"])
    assert sha256(parent_code / "code_manifest.json") == plan["parent_code_manifest_sha256"]
    assert sha256(parent_code / "plan.json") == plan["parent_plan_sha256"]
    assert sha256(parent_code / "horaz/src/src/exp236_source_duplicate_pairs.json") == SOURCE_DUPLICATE_MAP_SHA
    parent_config = json.loads((parent_run / "config.json").read_text())
    assert parent_config["code"] == str(parent_code)
    assert parent_config["run"] == str(parent_run)
    parent_result_path = parent_run / "output/result.json"
    assert sha256(parent_result_path) == plan["parent_result_sha256"]
    parent_result = json.loads(parent_result_path.read_text())
    previous = plan["parent_completed_epochs"]
    assert parent_result["status"] == f"PASS_EXP236_SOURCE_BLOCK_{previous}_OF_50"
    assert parent_result["completed_epochs"] == previous
    assert parent_result["target_data_opened"] is False
    assert parent_result["source_duplicate_policy"] == plan["source_duplicate_policy"]
    assert parent_result["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert parent_result["excluded_pairs_by_split"] == plan["excluded_pairs_by_split"]
    assert parent_result["removed_sampled_windows_by_split"] == plan["removed_sampled_windows_by_split"]
    assert parent_result["checkpoint_sha256"] == plan["parent_checkpoint_sha256"]
    exit_record = json.loads((parent_run / "exit.json").read_text())
    supervision = json.loads((parent_run / "supervision/complete.json").read_text())
    control = json.loads((parent_run / "supervision/control.json").read_text())
    assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
    assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert supervision["exit"] == exit_record
    assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
    assert Path(control["queue"]["run_path"]).resolve() == parent_run.resolve()
    assert sha256(parent) == plan["parent_checkpoint_sha256"]
    parent_history_path = parent.parent / "history.json"
    assert sha256(parent_history_path) == plan["parent_history_sha256"]
    parent_history = json.loads(parent_history_path.read_text())
    assert [row["epoch"] for row in parent_history] == list(range(1, previous + 1))

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    fold_dir = output / "fold0"
    fold_dir.mkdir()
    shutil.copy2(parent, fold_dir / "last.pt")
    assert sha256(fold_dir / "last.pt") == plan["parent_checkpoint_sha256"]
    (output / "contract.json").write_text(json.dumps(plan, indent=2) + "\n")
    sys.path.insert(0, str(code / "horaz/src/src"))
    guard = SourceAccessGuard(plan["train"] + plan["inner_validation"], output,
                              plan["data_root"])
    sys.addaudithook(guard)
    result = {"status": "RUNNING_EXP236_SOURCE_RESUME",
              "plan_sha256": args.plan_sha256,
              "parent_checkpoint_sha256": plan["parent_checkpoint_sha256"],
              "source_duplicate_policy": plan["source_duplicate_policy"],
              "source_duplicate_map_sha256": SOURCE_DUPLICATE_MAP_SHA,
              "excluded_pairs_by_split": plan["excluded_pairs_by_split"],
              "removed_sampled_windows_by_split": plan["removed_sampled_windows_by_split"],
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
        resolved.update(seed=3406, deterministic=False, epochs=50, num_workers=0,
                        torch_compile=False, max_iterations_per_epoch=None,
                        batch_size=4, max_frames=None,
                        output_root=plan["initial_output_root"])
        checkpoint_meta = torch.load(fold_dir / "last.pt", map_location="cpu",
                                     weights_only=True)
        assert {"model", "model_config", "optimizer", "rng_state", "epoch",
                "history", "resolved_config"} <= set(checkpoint_meta)
        assert checkpoint_meta["epoch"] == previous
        assert checkpoint_meta["resolved_config"] == resolved
        assert checkpoint_meta["history"] == parent_history
        del checkpoint_meta
        cfg = SimpleNamespace(**resolved)
        cfg.epochs = plan["block_end_epoch"]
        train.PERIODIC_EPOCHS = (cfg.epochs,)
        checkpoint = train.train_fold(cfg, 0, plan["train"],
                                      plan["inner_validation"], output, resolved,
                                      resume=True)
        history = json.loads((fold_dir / "history.json").read_text())
        assert [row["epoch"] for row in history] == list(range(1, cfg.epochs + 1))
        assert history[:previous] == parent_history
        assert all(row["training_iterations"] > 8 for row in history[previous:])
        assert all(math.isfinite(value) for row in history for value in row.values()
                   if isinstance(value, (int, float)))
        model, _ = load_checkpoint(checkpoint, torch.device("cpu"))
        assert all(torch.isfinite(value).all().item() for value in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        result.update(status=f"PASS_EXP236_SOURCE_BLOCK_{cfg.epochs}_OF_50",
                      elapsed_seconds=time.time() - started,
                      checkpoint_sha256=sha256(checkpoint),
                      checkpoint_reload="PASS_weights_only",
                      completed_epochs=cfg.epochs, planned_epochs=50,
                      history=history)
    except BaseException as exc:
        result.update(status="FAILED_EXP236_SOURCE_RESUME", error=repr(exc),
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
