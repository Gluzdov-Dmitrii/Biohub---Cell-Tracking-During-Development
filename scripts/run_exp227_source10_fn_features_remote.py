"""Execute once on pinned source8 graphs with CPU, memory and time limits."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/analyze_exp227_source10_fixed_node_ceiling.py"
SOURCE = ROOT / "scripts/analyze_exp227_source10_fn_features.py"
BASE_SHA = "1303739411b3ea5e3f1fc4dc6f7dbeff7b48ce2e995485f134413f813920a00b"
ATTR_RECEIPT = ROOT / "reports/exp227_source10_fixed_node_attribution_20260927.json"
ATTR_SHA = "d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7"
REPORT = ROOT / "reports/exp227_source10_fn_features_v3_20260927.json"
FAILURE = ROOT / "reports/exp227_source10_fn_features_failure_v3_20260927.json"
REMOTE_PYTHON = ("/home/scientists/gluz_d_s/kaggle/projects/"
                 "biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python")
REMOTE_COMMAND = ("ulimit -v 16777216; env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 "
                  "MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_DYNAMIC=FALSE "
                  "PYTHONDONTWRITEBYTECODE=1 timeout 2600s taskset -c 24-27 " +
                  REMOTE_PYTHON + " -")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not REPORT.exists() and not FAILURE.exists(), "Existing feature receipt needs reconciliation"
    assert sha(BASE) == BASE_SHA
    assert sha(ATTR_RECEIPT) == ATTR_SHA
    previous = json.loads(ATTR_RECEIPT.read_text())
    assert previous["status"] == "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION"
    assert previous["target6bba_access"] is False and previous["source_score"] == 0.8114014924249717
    marker = '\n\nif __name__ == "__main__":\n    main()\n'
    base = BASE.read_text(encoding="utf-8")
    assert base.endswith(marker)
    bundle = base[:-len(marker)] + "\n\n" + SOURCE.read_text(encoding="utf-8")
    bundle_sha = hashlib.sha256(bundle.encode()).hexdigest()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "nsu-quadro", REMOTE_COMMAND]
    try:
        process = subprocess.run(command, input=bundle, text=True, capture_output=True,
                                 timeout=2700, cwd=ROOT)
        if process.returncode:
            raise RuntimeError(f"remote CPU feature analysis exit {process.returncode}: {process.stderr[-4000:]}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_SOURCE10_FN_FEATURES"
        assert result["source_score"] == previous["source_score"]
        assert result["target6bba_access"] is False and result["candidate_tuning"] is False
        assert result["source_graph_gate"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
        assert len(result["movies"]) == 8 and result["endpoint_limited_fn"] == 153
        assert [row["dataset"] for row in result["movies"]] == [row["dataset"] for row in previous["rows"]]
        for row, old in zip(result["movies"], previous["rows"]):
            assert row["endpoint_limited_fn"] == old["endpoint_limited_fn"]
    except BaseException as exc:
        FAILURE.write_text(json.dumps({"status": "FAILED_EXP227_SOURCE10_FN_FEATURES",
                                       "error": repr(exc), "bundle_sha256": bundle_sha,
                                       "stderr_tail": process.stderr[-4000:] if "process" in locals() else None},
                                      indent=2) + "\n")
        raise
    result["analysis_bundle_sha256"] = bundle_sha
    result["analysis_feature_source_sha256"] = sha(SOURCE)
    result["parent_attribution_receipt_sha256"] = ATTR_SHA
    result["execution"] = {"host": "nsu-quadro", "cpu_affinity": "24-27",
                           "cuda_visible_devices": "", "memory_virtual_limit_gib": 16,
                           "timeout_seconds": 2600, "interpreter": REMOTE_PYTHON}
    REPORT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(REPORT),
                      "endpoint_limited_fn": result["endpoint_limited_fn"],
                      "distinct_endpoint_missed_nodes": result["distinct_endpoint_missed_nodes"],
                      "across_movies": result["across_movies"]}, allow_nan=False))


if __name__ == "__main__":
    main()
