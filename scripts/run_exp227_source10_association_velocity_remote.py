"""Run one pinned source8 half-velocity audit on bounded Quadro CPUs."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/analyze_exp227_source10_fixed_node_ceiling.py"
GEOMETRY_SOURCE = ROOT / "scripts/analyze_exp227_source10_association_geometry.py"
SOURCE = ROOT / "scripts/analyze_exp227_source10_association_velocity.py"
BASE_SHA = "1303739411b3ea5e3f1fc4dc6f7dbeff7b48ce2e995485f134413f813920a00b"
GEOMETRY_SOURCE_SHA = "ae39f7d75f41fffc7ad0be39d71b12b7d5dab0827837612353e2c426b1162f16"
OCCUPIED = ROOT / "reports/exp227_source10_occupied_links_20260927.json"
OCCUPIED_SHA = "7362f5c1ca1f3135828b050a50dc1086dd90b694556c9b3481552e59d656613d"
GEOMETRY = ROOT / "reports/exp227_source10_association_geometry_20260927.json"
GEOMETRY_SHA = "9e688773ee2f42f9c8a92cf6f34420a57338423d909ca4693402102458e64023"
REPORT = ROOT / "reports/exp227_source10_association_velocity_20260927.json"
FAILURE = ROOT / "reports/exp227_source10_association_velocity_failure_20260927.json"
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
    assert sha(BASE) == BASE_SHA and sha(GEOMETRY_SOURCE) == GEOMETRY_SOURCE_SHA
    assert sha(OCCUPIED) == OCCUPIED_SHA and sha(GEOMETRY) == GEOMETRY_SHA
    occupied = json.loads(OCCUPIED.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    assert occupied["status"] == "PASS_EXP227_SOURCE10_OCCUPIED_LINKS"
    assert geometry["status"] == "PASS_EXP227_SOURCE10_ASSOCIATION_GEOMETRY_AUDIT"
    assert geometry["totals"]["unmatched_only_cases"] == 69
    base_marker = '\n\nif __name__ == "__main__":\n    main()\n'
    geometry_marker = '\n\nif __name__ == "__main__":\n    print(json.dumps(main(), allow_nan=False))\n'
    base = BASE.read_text(encoding="utf-8")
    geometry_code = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    assert base.endswith(base_marker) and geometry_code.endswith(geometry_marker)
    occupied_injection = "\n\nPRIOR_OCCUPIED = json.loads(" + repr(json.dumps(occupied)) + ")\n"
    geometry_injection = ("\n\ngeometry_main = main\nPRIOR_GEOMETRY = json.loads(" +
                          repr(json.dumps(geometry)) + ")\n")
    bundle = (base[:-len(base_marker)] + occupied_injection + "\n" +
              geometry_code[:-len(geometry_marker)] + geometry_injection + "\n" +
              SOURCE.read_text(encoding="utf-8"))
    compile(bundle, "exp227_source10_association_velocity_bundle", "exec")
    bundle_sha = hashlib.sha256(bundle.encode()).hexdigest()
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
               "nsu-quadro", REMOTE_COMMAND]
    try:
        process = subprocess.run(command, input=bundle, text=True, capture_output=True,
                                 timeout=1900, cwd=ROOT)
        if process.returncode:
            raise RuntimeError(f"remote velocity audit exit {process.returncode}: {process.stderr[-4000:]}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_SOURCE10_ASSOCIATION_VELOCITY_AUDIT"
        assert result["source_score"] == geometry["source_score"]
        assert result["source_graph_gate"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
        assert result["target6bba_access"] is False and result["candidate_tuning"] is False
        assert len(result["rows"]) == 8
        assert [row["dataset"] for row in result["rows"]] == [row["dataset"] for row in geometry["rows"]]
        assert result["totals"]["all_cases"] == 69
        assert result["totals"]["required_advantage_cases"] == 20
        assert result["totals"]["required_movies_with_advantage"] == 4
        assert result["totals"]["valid_predecessor_cases"] == sum(
            row["valid_predecessor_cases"] for row in result["rows"])
        assert result["totals"]["advantage_cases"] == sum(row["advantage_cases"] for row in result["rows"])
        assert result["inputs"] == geometry["inputs"] and result["scorer_pins"] == geometry["scorer_pins"]
    except BaseException as exc:
        FAILURE.write_text(json.dumps({"status": "FAILED_EXP227_SOURCE10_ASSOCIATION_VELOCITY",
                                       "error": repr(exc), "bundle_sha256": bundle_sha,
                                       "stderr_tail": process.stderr[-4000:] if "process" in locals() else None},
                                      indent=2) + "\n", encoding="utf-8")
        raise
    result["analysis_bundle_sha256"] = bundle_sha
    result["analysis_source_sha256"] = sha(SOURCE)
    result["geometry_source_sha256"] = GEOMETRY_SOURCE_SHA
    result["prior_occupied_receipt_sha256"] = OCCUPIED_SHA
    result["prior_geometry_receipt_sha256"] = GEOMETRY_SHA
    result["execution"] = {"host": "nsu-quadro", "cpu_affinity": "24-27",
                           "cuda_visible_devices": "", "memory_virtual_limit_gib": 16,
                           "timeout_seconds": 1800, "interpreter": REMOTE_PYTHON}
    result["remote_stderr"] = process.stderr
    REPORT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(REPORT),
                      "totals": result["totals"],
                      "by_movie": [{"dataset": row["dataset"], "all": row["all_cases"],
                                    "valid": row["valid_predecessor_cases"],
                                    "advantage": row["advantage_cases"]} for row in result["rows"]]},
                     allow_nan=False))


if __name__ == "__main__":
    main()
