"""Resume the exact EXP227 source-only Horaz recipe from epoch 5 through 10."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, sha256
from run_exp226_source_pilot import write_training_report


PARENT_SHA = "c7ecfe2e4ff0f5c039cd4952fe43047e44ff60701016a3ebba3fd932aa543d2e"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"


def validate(plan):
    assert plan["experiment"] == "EXP227" and plan["purpose"] == "source_only_full_training_block02"
    assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
    assert plan["fold"] == 1 and plan["start_epoch"] == 6 and plan["block_end_epoch"] == 10
    assert plan["planned_epochs"] == 50 and plan["resume"] is True
    assert plan["checkpoint_selection"] == "deferred_source_graph_10_20_30_40_50"
    assert plan["parent_checkpoint_sha256"] == PARENT_SHA
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    train, inner = plan["train"], plan["inner_validation"]
    assert len(train) == 63 and len(inner) == 8
    names = [r["dataset_id"] for r in train + inner]
    assert len(names) == len(set(names)) == 71
    assert all(name.startswith("44b6_") for name in names)
    for row in train + inner:
        for key, suffix in (("zarr_path", ".zarr"), ("geff_path", ".geff")):
            assert Path(row[key]).name == row["dataset_id"] + suffix
    assert Path(plan["parent_checkpoint"]).name == "last.pt"
    assert Path(plan["output"]).name == "output"


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
    manifest = code / "source44_manifest.json"
    assert sha256(manifest) == SOURCE_MANIFEST_SHA
    source = json.loads(manifest.read_text())
    assert plan["train"] == source["train"]
    assert plan["inner_validation"] == source["inner_validation"]

    parent = Path(plan["parent_checkpoint"])
    parent_run = parent.parents[2]
    parent_result = json.loads((parent_run / "output/result.json").read_text())
    parent_exit = json.loads((parent_run / "exit.json").read_text())
    parent_supervision = json.loads((parent_run / "supervision/complete.json").read_text())
    assert parent_result["status"] == "PASS_FULL_SOURCE_BLOCK_5_OF_50"
    assert parent_result["target_data_opened"] is False
    assert parent_result["completed_epochs"] == 5
    assert parent_result["checkpoint_sha256"] == PARENT_SHA
    assert parent_exit["returncode"] == 0 and parent_exit["hard_timeout"] is False
    assert parent_supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert sha256(parent) == PARENT_SHA
    parent_history = json.loads((parent.parent / "history.json").read_text())
    assert [row["epoch"] for row in parent_history] == [1, 2, 3, 4, 5]
    assert sha256(parent.parent / "history.json") == plan["parent_history_sha256"]

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    fold_dir = output / "fold1"
    fold_dir.mkdir()
    shutil.copy2(parent, fold_dir / "last.pt")
    assert sha256(fold_dir / "last.pt") == PARENT_SHA
    (output / "contract.json").write_text(json.dumps(plan, indent=2) + "\n")
    sys.path.insert(0, str(code / "horaz/src/src"))
    guard = SourceAccessGuard(plan["train"] + plan["inner_validation"], output, plan["data_root"])
    sys.addaudithook(guard)
    result = {"status": "RUNNING_FULL_SOURCE_BLOCK02", "plan_sha256": args.plan_sha256,
              "parent_checkpoint_sha256": PARENT_SHA,
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
                        torch_compile=False, max_iterations_per_epoch=None, batch_size=4,
                        max_frames=None, output_root=str(parent_run / "output"))
        checkpoint_meta = torch.load(fold_dir / "last.pt", map_location="cpu", weights_only=True)
        assert checkpoint_meta["epoch"] == 5
        assert checkpoint_meta["resolved_config"] == resolved
        assert checkpoint_meta["history"] == parent_history
        del checkpoint_meta
        cfg = SimpleNamespace(**resolved)
        cfg.epochs = 10
        train.PERIODIC_EPOCHS = (10,)
        checkpoint = train.train_fold(cfg, 1, plan["train"], plan["inner_validation"],
                                      output, resolved, resume=True)
        history = json.loads((fold_dir / "history.json").read_text())
        assert [row["epoch"] for row in history] == list(range(1, 11))
        assert history[:5] == parent_history
        assert all(row["training_iterations"] > 8 for row in history[5:])
        assert all(math.isfinite(v) for row in history for v in row.values()
                   if isinstance(v, (int, float)))
        model, _ = load_checkpoint(checkpoint, torch.device("cpu"))
        assert all(torch.isfinite(v).all().item() for v in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        result.update(status="PASS_FULL_SOURCE_BLOCK_10_OF_50",
                      elapsed_seconds=time.time() - started,
                      checkpoint_sha256=sha256(checkpoint),
                      checkpoint_reload="PASS_weights_only",
                      completed_epochs=10, planned_epochs=50,
                      history=history)
    except BaseException as exc:
        result.update(status="FAILED_FULL_SOURCE_BLOCK02", error=repr(exc),
                      elapsed_seconds=time.time() - started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids), denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else "attempt_blocked")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({k: v for k, v in result.items() if k != "history"}), flush=True)


if __name__ == "__main__":
    main()
