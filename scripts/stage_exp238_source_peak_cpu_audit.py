"""One-shot EXP238 source peak CPU bundle stage; default is local review only."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh

if not __debug__:
    raise RuntimeError("EXP238 staging requires assertions; PYTHONOPTIMIZE must be 0")


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp238_source_peak_cpu_audit_20260927"
MANIFEST = BUNDLE / "manifest.json"
CODE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp238_source_peak_cpu_audit_v1_20260927"
RUN = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp238_source_peak_cpu_audit_v1_20260927"
INTENT = ROOT / "reports/exp238_source_peak_cpu_audit_stage_intent_20260927.json"
RECEIPT = ROOT / "reports/exp238_source_peak_cpu_audit_stage_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_json(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def local_gate() -> tuple[dict, dict]:
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((BUNDLE / "config.json").read_text())
    assert manifest["status"] == "SEALED_EXP238_SOURCE_PEAK_CPU_AUDIT_LOCAL_ONLY"
    assert config["status"] == "PREREGISTERED_EXP238_SOURCE_PEAK_CPU_LOCAL_ONLY"
    assert config["output"] == RUN + "/output"
    assert [row["cache_cohort"] for row in config["cohorts"]] == ["source44", "source6"]
    required = {"audit_exp238_source_peaks.py", "config.json", "baseline/manifest.json",
                "verification/source44.json", "verification/source6.json",
                "verification/source44_guarded_recheck.json",
                "verification/source44_optimization_correction.json"}
    assert required <= set(manifest["files"])
    assert {path.relative_to(BUNDLE).as_posix() for path in BUNDLE.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and not any(part.startswith("pytest_tmp") for part in path.parts)} == \
        set(manifest["files"]) | {"manifest.json"}
    for relative, digest in manifest["files"].items():
        path = (BUNDLE / relative).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and sha(path) == digest
    for cohort in config["cohorts"]:
        for field in ("status_sha256", "exit_sha256", "complete_sha256",
                      "control_sha256", "independent_receipt_sha256"):
            value = cohort[field]
            assert isinstance(value, str) and len(value) == 64
        copied = BUNDLE / "verification" / (cohort["cache_cohort"] + ".json")
        assert sha(copied) == cohort["independent_receipt_sha256"]
        receipt = json.loads(copied.read_text())
        assert receipt["status"] == "PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION"
        assert receipt["ordered_ids"] == cohort["ids"]
        assert receipt["status_sha256"] == cohort["status_sha256"]
        assert receipt["plan_sha256"] == cohort["plan_sha256"]
        assert receipt["manifest_sha256"] == cohort["manifest_sha256"]
        assert receipt["exit0"] and receipt["released"] and receipt["all_graph_hashes_exact"]
        assert receipt["source_only"] and not receipt["labels_read"]
    guarded = config["cohorts"][0]["guarded_recheck_receipt_sha256"]
    assert isinstance(guarded, str) and len(guarded) == 64
    assert sha(BUNDLE / "verification/source44_guarded_recheck.json") == guarded
    correction = config["cohorts"][0]["optimization_correction_receipt_sha256"]
    assert isinstance(correction, str) and len(correction) == 64
    assert sha(BUNDLE / "verification/source44_optimization_correction.json") == correction
    return manifest, config


def remote_preflight() -> dict:
    source = r'''import json,os,pathlib,sys
if not __debug__:raise RuntimeError('Assertions disabled')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
print(json.dumps({'status':'PASS_EXP238_CPU_STAGE_PREFLIGHT_NO_LABELS',
 'code_absent':True,'run_absent':True,'labels_read':False}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN))
    assert "@@" not in source
    return ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -", source)


def remote_stage(manifest: dict, manifest_sha: str) -> dict:
    bodies = {relative: base64.b64encode((BUNDLE / relative).read_bytes()).decode("ascii")
              for relative in manifest["files"]}
    bodies["manifest.json"] = base64.b64encode(MANIFEST.read_bytes()).decode("ascii")
    expected = {**manifest["files"], "manifest.json": manifest_sha}
    source = r'''import ast,base64,hashlib,json,os,pathlib
if not __debug__:raise RuntimeError('Assertions disabled')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
bodies=@@BODIES@@;expected=@@EXPECTED@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
code.mkdir(parents=True,exist_ok=False)
for name,encoded in bodies.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(encoded,validate=True))
 assert sha(path)==expected[name],name
 if name.endswith('.py'):ast.parse(path.read_text(),filename=name)
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
print(json.dumps({'status':'STAGED_EXP238_CPU_AUDIT_NO_LABELS','code':str(code),
 'manifest_sha256':sha(code/'manifest.json'),'files':len(observed),
 'run_absent':True,'labels_read':False}))
'''
    for token, value in {"@@CODE@@": CODE, "@@RUN@@": RUN,
                         "@@BODIES@@": bodies, "@@EXPECTED@@": expected}.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "exp238_cpu_remote_stage", "exec")
    return ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -", source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        config = json.loads((BUNDLE / "config.json").read_text())
        print(json.dumps({"status": "EXP238_CPU_STAGE_LOCAL_REVIEW_ONLY",
                          "dynamic_pins_ready": all(row["status_sha256"] for row in config["cohorts"])
                          and bool(config["cohorts"][0]["guarded_recheck_receipt_sha256"]),
                          "remote_mutation": False}))
        return
    manifest, config = local_gate()
    assert not INTENT.exists() and not RECEIPT.exists()
    preflight = remote_preflight()
    assert preflight["status"] == "PASS_EXP238_CPU_STAGE_PREFLIGHT_NO_LABELS"
    manifest_sha = sha(MANIFEST)
    exclusive_json(INTENT, {"status": "INTENT_EXP238_CPU_STAGE",
                            "manifest_sha256": manifest_sha,
                            "config_sha256": sha(BUNDLE / "config.json"),
                            "preflight": preflight, "labels_read": False})
    staged = remote_stage(manifest, manifest_sha)
    assert staged["status"] == "STAGED_EXP238_CPU_AUDIT_NO_LABELS"
    assert staged["manifest_sha256"] == manifest_sha
    exclusive_json(RECEIPT, {"status": "STAGED_EXP238_CPU_AUDIT_NO_LABELS",
                             "manifest_sha256": manifest_sha,
                             "config_sha256": sha(BUNDLE / "config.json"),
                             "intent_sha256": sha(INTENT), "remote": staged,
                             "run_started": False, "labels_read": False})
    print(json.dumps({"status": staged["status"], "manifest_sha256": manifest_sha}))


if __name__ == "__main__":
    main()
