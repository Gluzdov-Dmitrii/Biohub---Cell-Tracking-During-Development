"""Run the pinned source8 attribution once on a CPU-only remote interpreter."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/analyze_exp227_source10_fixed_node_ceiling.py"
REPORT = ROOT / "reports/exp227_source10_fixed_node_attribution_20260927.json"
FAILURE = ROOT / "reports/exp227_source10_fixed_node_attribution_failure_20260927.json"
REMOTE_PYTHON = ("/home/scientists/gluz_d_s/kaggle/projects/"
                 "biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python")
REMOTE_COMMAND = ("env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 "
                  "OPENBLAS_NUM_THREADS=4 MKL_DYNAMIC=FALSE PYTHONDONTWRITEBYTECODE=1 "
                  "taskset -c 24-27 " + REMOTE_PYTHON + " -")


def main():
    assert not REPORT.exists() and not FAILURE.exists(), "Existing attribution receipt needs reconciliation"
    source = SOURCE.read_text(encoding="utf-8")
    source_sha = hashlib.sha256(source.encode()).hexdigest()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "nsu-quadro", REMOTE_COMMAND]
    try:
        process = subprocess.run(command, input=source, text=True, capture_output=True,
                                 timeout=1800, cwd=ROOT)
        if process.returncode:
            raise RuntimeError(f"remote CPU attribution exit {process.returncode}: {process.stderr[-2000:]}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION"
        assert result["target6bba_access"] is False and result["candidate_tuning"] is False
        assert len(result["rows"]) == 8
    except BaseException as exc:
        FAILURE.write_text(json.dumps({"status": "FAILED_EXP227_SOURCE10_FIXED_NODE_ATTRIBUTION",
                                       "error": repr(exc), "analysis_source_sha256": source_sha},
                                      indent=2) + "\n")
        raise
    result["analysis_source_sha256"] = source_sha
    result["execution"] = {"host": "nsu-quadro", "cpu_affinity": "24-27",
                           "cuda_visible_devices": "", "interpreter": REMOTE_PYTHON}
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "source_score": result["source_score"],
                      "optimistic": result["optimistic"], "pooled": {
                          key: result["pooled"][key] for key in
                          ("gt_edges", "edge_fn", "endpoint_limited_fn", "association_limited_fn",
                           "edge_fp", "division_tp", "division_fp", "division_fn")},
                      "report": str(REPORT)}))


if __name__ == "__main__":
    main()
