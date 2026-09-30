"""Infer one frozen EXP234 reciprocal target shard without opening labels."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from exp234_source_scope import validate_scope
from score_exp214_paired import read_graphs


THRESHOLDS = ("0.900", "0.940", "0.965")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(plan):
    assert plan["experiment"] == "EXP234_TARGET_CHUNK"
    source = plan["source_embryo"]
    assert source in ("44b6", "6bba")
    target = "6bba" if source == "44b6" else "44b6"
    assert plan["target_embryo"] == target
    assert plan["selected_threshold"] in THRESHOLDS
    assert plan["chunk_count"] == (8 if source == "44b6" else 4)
    assert 0 <= plan["chunk_index"] < plan["chunk_count"]

    code = Path(plan["code"])
    manifest = json.loads((code / "code_manifest.json").read_text())
    for name, digest in manifest.items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest, name
    assert sha(plan["assignment"]) == plan["assignment_sha256"]
    assignment = json.loads(Path(plan["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["canonical_cohort_manifest_sha256"] == plan["cohort_sha256"]
    assert assignment["directions"][source]["target_embryo"] == target
    chunks = assignment["directions"][source]["chunks"]
    assert len(chunks) == plan["chunk_count"]
    all_movies = [name for chunk in chunks for name in chunk]
    assert len(all_movies) == (116 if source == "44b6" else 59)
    assert len(set(all_movies)) == len(all_movies)
    assert all(name.startswith(target + "_") for name in all_movies)
    assert all(len(chunk) in (14, 15) for chunk in chunks)

    assert sha(plan["movies"]) == plan["movies_sha256"]
    movies = json.loads(Path(plan["movies"]).read_text())
    assert movies == chunks[plan["chunk_index"]]
    assert len(movies) in (14, 15) and len(movies) == len(set(movies))
    assert all(name.startswith(target + "_") for name in movies)

    assert sha(plan["source_selection_result"]) == plan["source_selection_result_sha256"]
    selection = json.loads(Path(plan["source_selection_result"]).read_text())
    assert selection["status"] == "PASS_EXP234_SOURCE_THRESHOLD_SELECTED"
    assert selection["source_embryo"] == source
    assert selection["selected_threshold"] == plan["selected_threshold"]

    assert sha(plan["source_bundle"]) == plan["source_bundle_sha256"]
    source_bundle = json.loads(Path(plan["source_bundle"]).read_text())
    assert sha(plan["bundle"]) == plan["bundle_sha256"]
    bundle = json.loads(Path(plan["bundle"]).read_text())
    assert bundle["source_embryo"] == source
    assert bundle["evaluation_mode"] == "EXP234_TARGET_ROLLOUT"
    validate_scope(bundle, movies)
    for role in ("primary", "secondary", "center"):
        assert bundle[role] == source_bundle[role]
        assert sha(bundle[role]["path"]) == bundle[role]["sha256"]
    for key in ("source_train_movies", "source_validation_movies", "center_seen_movies"):
        assert bundle[key] == source_bundle[key]
        assert not set(movies).intersection(bundle[key])
    assert sha(plan["notebook"]) == plan["notebook_sha256"]
    return code, bundle, movies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    code, bundle, movies = validate_plan(plan)
    output = Path(plan["output"])
    assert not output.exists(), "Target chunk output already exists"
    started = time.time()
    command = [sys.executable, str(code / "run_exp214_public_fold.py"),
               "--notebook", plan["notebook"], "--repo", plan["repo"],
               "--bundle", plan["bundle"], "--data-dir", plan["data_dir"],
               "--movies", plan["movies"], "--output", str(output),
               "--override-env", "BIOHUB_DET_THRESHOLD=" + plan["selected_threshold"]]
    subprocess.run(command, check=True)
    receipt_path = output / "inference_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "PASS_FROZEN_PUBLIC_FAMILY_INFERENCE"
    assert receipt["target_labels_read"] is False
    assert receipt["movies"] == movies and receipt["bundle"] == bundle
    assert receipt["notebook_sha256"] == plan["notebook_sha256"]
    assert receipt["override_env"] == {"BIOHUB_DET_THRESHOLD": plan["selected_threshold"]}
    assert sha(output / "submission.csv") == receipt["submission_sha256"]
    graphs = read_graphs(output / "submission.csv")
    assert set(graphs) == set(movies)
    status = {"status": "PASS_EXP234_TARGET_CHUNK_NO_LABELS", "source_embryo": plan["source_embryo"],
              "target_embryo": plan["target_embryo"], "chunk_index": plan["chunk_index"],
              "movies": movies, "selected_threshold": plan["selected_threshold"],
              "plan_sha256": args.plan_sha256, "source_selection_result_sha256": plan["source_selection_result_sha256"],
              "csv_sha256": receipt["submission_sha256"], "receipt_sha256": sha(receipt_path),
              "target_labels_read": False, "elapsed_seconds": time.time() - started}
    (output / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps({"status": status["status"], "source": plan["source_embryo"],
                      "chunk": plan["chunk_index"], "movies": len(movies),
                      "elapsed_seconds": status["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
