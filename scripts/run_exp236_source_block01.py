"""Three full scratch Horaz epochs on source6bba, with target44b6 excluded."""
import argparse
import json
import math
from pathlib import Path, PurePosixPath
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, sha256
from run_exp226_source_pilot import write_training_report


SOURCE_BUNDLE = ("/home/scientists/gluz_d_s/kaggle/projects/"
                 "biohub-cell-tracking-during-development/code/"
                 "exp234_source_threshold_v2_20260926/6bba_bundle.json")
SOURCE_BUNDLE_SHA = "90e95a45a4d58a72c18495b48c979de52afdc080b9070892c53e8bf41c2f59b1"


def validate(plan):
    assert plan["experiment"] == "EXP236"
    assert plan["purpose"] == "source_only_reciprocal_horaz_block01"
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    assert plan["fold"] == 0 and plan["block_end_epoch"] == 3
    assert plan["planned_epochs"] == 50 and plan["resume"] is False
    assert plan["checkpoint_selection"] == "deferred_source_graph_10_20_30_40_50"
    assert plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert Path(plan["output"]).name == "output"
    train, inner = plan["train"], plan["inner_validation"]
    assert len(train) == 115 and len(inner) == 11
    ids = [row["dataset_id"] for row in train + inner]
    assert len(ids) == len(set(ids)) == 126
    assert all(name.startswith("6bba_") for name in ids)
    data_root = PurePosixPath(plan["data_root"])
    for row in train + inner:
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
    manifest = code / "source6bba_manifest.json"
    assert sha256(manifest) == plan["source_manifest_sha256"]
    source = json.loads(manifest.read_text())
    assert plan["train"] == source["train"]
    assert plan["inner_validation"] == source["inner_validation"]
    assert sha256(SOURCE_BUNDLE) == SOURCE_BUNDLE_SHA
    bundle = json.loads(Path(SOURCE_BUNDLE).read_text())
    assert [r["dataset_id"] for r in plan["train"]] == bundle["source_train_movies"]
    assert [r["dataset_id"] for r in plan["inner_validation"]] == bundle["source_validation_movies"]

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(code / "horaz/src/src"))
    guard = SourceAccessGuard(plan["train"] + plan["inner_validation"], output, plan["data_root"])
    sys.addaudithook(guard)
    result = {"status": "RUNNING_EXP236_SOURCE_BLOCK01", "plan_sha256": args.plan_sha256,
              "source_bundle_sha256": SOURCE_BUNDLE_SHA,
              "no_generalization_claim": True,
              "checkpoint_selection": plan["checkpoint_selection"]}
    (output / "contract.json").write_text(json.dumps(plan, indent=2) + "\n")
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
                        torch_compile=False, max_iterations_per_epoch=None, batch_size=4,
                        max_frames=None, output_root=str(output))
        cfg = SimpleNamespace(**resolved)
        cfg.epochs = 3
        train.PERIODIC_EPOCHS = (1, 2, 3)
        checkpoint = train.train_fold(cfg, 0, plan["train"], plan["inner_validation"],
                                      output, resolved, resume=False)
        history = json.loads((output / "fold0/history.json").read_text())
        assert [row["epoch"] for row in history] == [1, 2, 3]
        assert all(row["training_iterations"] > 8 for row in history)
        assert all(math.isfinite(value) for row in history for value in row.values()
                   if isinstance(value, (int, float)))
        model, _ = load_checkpoint(checkpoint, torch.device("cpu"))
        assert all(torch.isfinite(value).all().item() for value in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        result.update(status="PASS_EXP236_SOURCE_BLOCK_3_OF_50",
                      elapsed_seconds=time.time() - started,
                      checkpoint_sha256=sha256(checkpoint),
                      checkpoint_reload="PASS_weights_only",
                      completed_epochs=3, planned_epochs=50, history=history)
    except BaseException as exc:
        result.update(status="FAILED_EXP236_SOURCE_BLOCK01", error=repr(exc),
                      elapsed_seconds=time.time() - started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids), denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else "attempt_blocked")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({key: value for key, value in result.items() if key != "history"}),
              flush=True)


if __name__ == "__main__":
    main()
