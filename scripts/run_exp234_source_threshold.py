"""Produce three sealed source-validation graph arms without opening labels."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from exp234_source_scope import validate_scope


THRESHOLDS = ("0.900", "0.940", "0.965")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    assert plan["experiment"] == "EXP234" and tuple(plan["thresholds"]) == THRESHOLDS
    code = Path(plan["code"])
    manifest = json.loads((code / "code_manifest.json").read_text())
    for name, digest in manifest.items():
        assert sha(code / name) == digest, name
    assert sha(plan["notebook"]) == plan["notebook_sha256"]
    assert sha(plan["bundle"]) == plan["bundle_sha256"]
    assert sha(plan["movies"]) == plan["movies_sha256"]
    bundle = json.loads(Path(plan["bundle"]).read_text())
    movies = json.loads(Path(plan["movies"]).read_text())
    validate_scope(bundle, movies)
    assert bundle["source_embryo"] == plan["source_embryo"]
    assert len(movies) == plan["movie_count"]
    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    records = []
    for threshold in THRESHOLDS:
        arm = output / ("threshold_" + threshold.replace(".", ""))
        command = [sys.executable, str(code / "run_exp214_public_fold.py"),
                   "--notebook", plan["notebook"], "--repo", plan["repo"],
                   "--bundle", plan["bundle"], "--data-dir", plan["data_dir"],
                   "--movies", plan["movies"], "--output", str(arm),
                   "--override-env", "BIOHUB_DET_THRESHOLD=" + threshold]
        subprocess.run(command, check=True)
        receipt = json.loads((arm / "inference_receipt.json").read_text())
        assert receipt["status"] == "PASS_FROZEN_PUBLIC_FAMILY_INFERENCE"
        assert receipt["target_labels_read"] is False
        assert receipt["override_env"] == {"BIOHUB_DET_THRESHOLD": threshold}
        assert receipt["movies"] == movies
        assert sha(arm / "submission.csv") == receipt["submission_sha256"]
        records.append({"threshold": threshold, "csv": str(arm / "submission.csv"),
                        "csv_sha256": receipt["submission_sha256"],
                        "receipt_sha256": sha(arm / "inference_receipt.json")})
    result = {"status": "PASS_EXP234_SOURCE_ARMS_NO_LABELS", "experiment": "EXP234",
              "source_embryo": plan["source_embryo"], "movies": movies,
              "thresholds": list(THRESHOLDS), "records": records,
              "target_labels_read": False, "elapsed_seconds": time.time() - started,
              "plan_sha256": args.plan_sha256}
    (output / "status.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source": plan["source_embryo"],
                      "movies": len(movies), "elapsed_seconds": result["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
