"""Run one pinned source8 occupied-link audit with CPU/memory/time bounds."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/analyze_exp227_source10_fixed_node_ceiling.py"
SOURCE = ROOT / "scripts/analyze_exp227_source10_occupied_links.py"
BASE_SHA = "1303739411b3ea5e3f1fc4dc6f7dbeff7b48ce2e995485f134413f813920a00b"
ATTR_RECEIPT = ROOT / "reports/exp227_source10_fixed_node_attribution_20260927.json"
ATTR_SHA = "d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7"
GAP_RECEIPT = ROOT / "reports/exp227_source10_gap_feasibility_20260927.json"
GAP_SHA = "605c7f04129dc3613d582a6b4845bc5d47673af1955042b7d78785f8951d3b8a"
REPORT = ROOT / "reports/exp227_source10_occupied_links_20260927.json"
FAILURE = ROOT / "reports/exp227_source10_occupied_links_failure_20260927.json"
REMOTE_PYTHON = ("/home/scientists/gluz_d_s/kaggle/projects/"
                 "biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python")
REMOTE_COMMAND = ("ulimit -v 16777216; env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 "
                  "MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_DYNAMIC=FALSE "
                  "PYTHONDONTWRITEBYTECODE=1 timeout 1800s taskset -c 24-27 " +
                  REMOTE_PYTHON + " -")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not REPORT.exists() and not FAILURE.exists(), "Existing audit receipt requires reconciliation"
    assert sha(BASE) == BASE_SHA and sha(ATTR_RECEIPT) == ATTR_SHA and sha(GAP_RECEIPT) == GAP_SHA
    gap = json.loads(GAP_RECEIPT.read_text())
    assert gap["status"] == "PASS_EXP227_SOURCE10_GAP_FEASIBILITY"
    assert gap["totals"]["stages"]["anchors_supported"] == 20
    assert gap["totals"]["topology_only_edge_fn_upper_bound"] == 0
    marker = '\n\nif __name__ == "__main__":\n    main()\n'
    base = BASE.read_text(encoding="utf-8")
    assert base.endswith(marker)
    bundle = base[:-len(marker)] + "\n\n" + SOURCE.read_text(encoding="utf-8")
    bundle_sha = hashlib.sha256(bundle.encode()).hexdigest()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "nsu-quadro", REMOTE_COMMAND]
    try:
        process = subprocess.run(command, input=bundle, text=True, capture_output=True,
                                 timeout=1900, cwd=ROOT)
        if process.returncode:
            raise RuntimeError(f"remote occupied-link audit exit {process.returncode}: {process.stderr[-4000:]}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_SOURCE10_OCCUPIED_LINKS"
        assert result["source_score"] == gap["source_score"]
        assert result["target6bba_access"] is False and result["candidate_tuning"] is False
        assert result["source_graph_gate"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
        assert len(result["rows"]) == 8
        assert [row["dataset"] for row in result["rows"]] == [row["dataset"] for row in gap["rows"]]
        for row, previous in zip(result["rows"], gap["rows"]):
            assert row["stages"].get("occupied_anchor_gaps", 0) == previous["stages"].get("anchors_supported", 0)
            assert row["stages"].get("pred_gap_still_open", 0) == 0
        assert result["totals"]["occupied_anchor_gaps"] == 20
        assert result["totals"]["association_limited_fn"] == 87
    except BaseException as exc:
        FAILURE.write_text(json.dumps({"status": "FAILED_EXP227_SOURCE10_OCCUPIED_LINKS",
                                       "error": repr(exc), "bundle_sha256": bundle_sha,
                                       "stderr_tail": process.stderr[-4000:] if "process" in locals() else None},
                                      indent=2) + "\n")
        raise
    result["analysis_bundle_sha256"] = bundle_sha
    result["analysis_source_sha256"] = sha(SOURCE)
    result["gap_feasibility_receipt_sha256"] = GAP_SHA
    result["execution"] = {"host": "nsu-quadro", "cpu_affinity": "24-27",
                           "cuda_visible_devices": "", "memory_virtual_limit_gib": 16,
                           "timeout_seconds": 1800, "interpreter": REMOTE_PYTHON}
    REPORT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(REPORT),
                      "totals": result["totals"],
                      "rows": [{"dataset": row["dataset"],
                                "occupied": len(row["occupied_details"]),
                                "patterns": row["occupied_patterns"],
                                "assoc_fn": row["association_limited_fn"],
                                "assoc_classes": row["association_source_outgoing_classes"]}
                               for row in result["rows"]]}, allow_nan=False))


if __name__ == "__main__":
    main()
