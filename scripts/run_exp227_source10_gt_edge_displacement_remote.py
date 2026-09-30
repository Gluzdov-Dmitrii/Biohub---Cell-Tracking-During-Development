"""Run one preregistered source8 GT-motion audit on bounded Quadro CPUs."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/analyze_exp227_source10_fixed_node_ceiling.py"
SOURCE = ROOT / "scripts/analyze_exp227_source10_gt_edge_displacement.py"
ATTR = ROOT / "reports/exp227_source10_fixed_node_attribution_20260927.json"
OCCUPIED = ROOT / "reports/exp227_source10_occupied_links_20260927.json"
BASE_SHA = "1303739411b3ea5e3f1fc4dc6f7dbeff7b48ce2e995485f134413f813920a00b"
ATTR_SHA = "d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7"
OCCUPIED_SHA = "7362f5c1ca1f3135828b050a50dc1086dd90b694556c9b3481552e59d656613d"
REPORT = ROOT / "reports/exp227_source10_gt_edge_displacement_20260927.json"
FAILURE = ROOT / "reports/exp227_source10_gt_edge_displacement_failure_20260927.json"
REMOTE_PYTHON = ("/home/scientists/gluz_d_s/kaggle/projects/"
                 "biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python")
REMOTE_COMMAND = ("ulimit -v 16777216; env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 "
                  "MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_DYNAMIC=FALSE "
                  "PYTHONDONTWRITEBYTECODE=1 timeout 1800s taskset -c 24-27 " +
                  REMOTE_PYTHON + " -")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not REPORT.exists() and not FAILURE.exists(), "Existing receipt requires reconciliation"
    assert sha(BASE) == BASE_SHA and sha(ATTR) == ATTR_SHA and sha(OCCUPIED) == OCCUPIED_SHA
    assert "EXP227 GT edge displacement diagnostic preregistration" in (
        ROOT / "EXPERIMENTS.md").read_text(encoding="utf-8")
    attr = json.loads(ATTR.read_text(encoding="utf-8"))
    occupied = json.loads(OCCUPIED.read_text(encoding="utf-8"))
    assert attr["status"] == "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION"
    assert occupied["status"] == "PASS_EXP227_SOURCE10_OCCUPIED_LINKS"
    assert attr["pooled"]["gt_edges"] == 2039
    assert occupied["totals"]["association_limited_fn"] == 87
    assert [row["dataset"] for row in attr["rows"]] == [
        row["dataset"] for row in occupied["rows"]]
    prior_occupied = {"status": occupied["status"], "totals": occupied["totals"],
                      "rows": [{"dataset": row["dataset"],
                                "association_details": row["association_details"]}
                               for row in occupied["rows"]]}
    marker = '\n\nif __name__ == "__main__":\n    main()\n'
    base = BASE.read_text(encoding="utf-8")
    assert base.endswith(marker)
    injections = ("\n\nPRIOR_ATTR = json.loads(" + repr(json.dumps(attr)) + ")\n" +
                  "PRIOR_OCCUPIED = json.loads(" + repr(json.dumps(prior_occupied)) + ")\n")
    bundle = base[:-len(marker)] + injections + "\n" + SOURCE.read_text(encoding="utf-8")
    compile(bundle, "exp227_source10_gt_edge_displacement_bundle", "exec")
    bundle_sha = hashlib.sha256(bundle.encode()).hexdigest()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "nsu-quadro", REMOTE_COMMAND]
    try:
        process = subprocess.run(command, input=bundle, text=True, capture_output=True,
                                 timeout=1900, cwd=ROOT)
        if process.returncode:
            raise RuntimeError(f"remote displacement audit exit {process.returncode}: {process.stderr[-4000:]}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_SOURCE10_GT_EDGE_DISPLACEMENT_AUDIT"
        assert result["source_score"] == attr["source_score"]
        assert result["source_graph_gate"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
        assert result["target6bba_access"] is False and result["candidate_tuning"] is False
        assert len(result["rows"]) == 8
        assert [row["dataset"] for row in result["rows"]] == [row["dataset"] for row in attr["rows"]]
        assert result["pooled"]["gt_edges"] == 2039
        assert result["pooled"]["class_counts_all_edges"] == {
            "tp": 1799, "endpoint_limited_fn": 153, "association_limited_fn": 87}
        assert result["inputs"] == [
            {"dataset": row["dataset"],
             "graph_csv_sha256": row["graph_csv_sha256"],
             "graph_receipt_sha256": row["graph_receipt_sha256"],
             "gt_geff_tree_sha256": row["gt_geff_tree_sha256"],
             "gt_files": row["gt_files"]} for row in attr["inputs"]["rows"]]
    except BaseException as exc:
        FAILURE.write_text(json.dumps({"status": "FAILED_EXP227_SOURCE10_GT_EDGE_DISPLACEMENT",
                                       "error": repr(exc), "bundle_sha256": bundle_sha,
                                       "stderr_tail": process.stderr[-4000:] if "process" in locals() else None},
                                      indent=2) + "\n", encoding="utf-8")
        raise
    result["analysis_bundle_sha256"] = bundle_sha
    result["analysis_source_sha256"] = sha(SOURCE)
    result["prior_attribution_receipt_sha256"] = ATTR_SHA
    result["prior_occupied_receipt_sha256"] = OCCUPIED_SHA
    result["execution"] = {"host": "nsu-quadro", "cpu_affinity": "24-27",
                           "cuda_visible_devices": "", "memory_virtual_limit_gib": 16,
                           "timeout_seconds": 1800, "interpreter": REMOTE_PYTHON}
    result["remote_stderr"] = process.stderr
    REPORT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(REPORT),
                      "pooled": result["pooled"],
                      "by_movie": [{"dataset": row["dataset"],
                                    "gt_edges": row["gt_edges"],
                                    "nonconsecutive": row["nonconsecutive_gt_edges"],
                                    "association_fn_median_um": row["displacement_um"]["association_limited_fn"]["median"],
                                    "tp_median_um": row["displacement_um"]["tp"]["median"],
                                    "recall_by_distance": row["recall_by_distance"],
                                    "direction_consistent": row["direction_consistent"]}
                                   for row in result["rows"]]}, allow_nan=False))


if __name__ == "__main__":
    main()
