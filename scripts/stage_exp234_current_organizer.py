"""One-shot source staging for the separate current-organizer EXP234 rescore."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
SCALE_AUDIT = ROOT / "reports/exp234_current_image_scale_audit_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_organizer_stage_20260927.json"
EXPECTED_SCALE_SHA = "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not RECEIPT.exists(), "Stage receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    audit = json.loads(SCALE_AUDIT.read_text())
    assert prepared["status"] == "PREPARED_EXP234_CURRENT_ORGANIZER_TARGET175_NO_LABELS_LOCAL_ONLY"
    assert sha(SCALE_AUDIT) == EXPECTED_SCALE_SHA
    assert audit["status"] == "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS"
    assert audit["count"] == 175 and audit["target_labels_read"] is False
    assert sha(ROOT / "reports/EXP234_CURRENT_ORGANIZER_METRIC_PREREG_20260927.md") == (
        "a2a8a6b79739e13111df98c300d03efd029920e79c9893bb7c65587164939cec")
    for name, digest in prepared["prerequisite_local_sha256"].items():
        assert sha(ROOT / name) == digest, name
    bundle = Path(prepared["bundle"])
    assert sha(bundle / "code_manifest.json") == prepared["code_manifest_sha256"]
    manifest = json.loads((bundle / "code_manifest.json").read_text())
    assert manifest == prepared["source_hashes"]
    files = {name: base64.b64encode((bundle / name).read_bytes()).decode()
             for name in sorted([*manifest, "code_manifest.json", "score_config.json"])}
    assert sha(bundle / "score_config.json") == prepared["score_config_sha256"]
    config = json.loads((bundle / "score_config.json").read_text())
    assert config["code"] == prepared["remote_code_intended"]
    assert config["run"] == prepared["remote_run_intended"]
    assert config["python"] == prepared["interpreter_intended"]
    assert config["historical_gate_sha256"] == prepared["historical_gate_sha256"]
    assert config["historical_result_sha256"] == prepared["historical_result_sha256"]

    source = r'''import base64,hashlib,json,os,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@);env=pathlib.Path(@@ENV@@)
old_code=pathlib.Path(@@OLD_CODE@@);old_gate=pathlib.Path(@@OLD_GATE@@)
old_result=pathlib.Path(@@OLD_RESULT@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists() and not env.exists()
assert sha(old_code/'code_manifest.json')==@@OLD_MANIFEST_SHA@@
assert sha(old_code/'score_config.json')==@@OLD_CONFIG_SHA@@
assert sha(old_gate)==@@OLD_GATE_SHA@@ and sha(old_result)==@@OLD_RESULT_SHA@@
assert json.loads(old_gate.read_text())['status']=='PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS'
assert json.loads(old_result.read_text())['status']=='PASS_EXP234_SOURCE_SELECTED_TARGET175'
print(json.dumps({'status':'PASS_EXP234_CURRENT_ORGANIZER_STAGE_PREFLIGHT',
                  'historical_gate_sha256':sha(old_gate),'historical_result_sha256':sha(old_result),
                  'remote_code_absent':True,'remote_run_absent':True,'remote_env_absent':True}))
'''
    replacement = {
        "@@CODE@@": repr(config["code"]), "@@RUN@@": repr(config["run"]),
        "@@ENV@@": repr(str(Path(config["python"]).parent.parent)),
        "@@OLD_CODE@@": repr(config["historical_code"]),
        "@@OLD_GATE@@": repr(config["historical_gate"]),
        "@@OLD_RESULT@@": repr(config["historical_result"]),
        "@@OLD_MANIFEST_SHA@@": repr(config["historical_manifest_sha256"]),
        "@@OLD_CONFIG_SHA@@": repr(config["historical_config_sha256"]),
        "@@OLD_GATE_SHA@@": repr(config["historical_gate_sha256"]),
        "@@OLD_RESULT_SHA@@": repr(config["historical_result_sha256"]),
    }
    for token, value in replacement.items():
        source = source.replace(token, value)
    preflight = ssh("nsu-quadro", "python3 -", source)
    assert preflight["status"] == "PASS_EXP234_CURRENT_ORGANIZER_STAGE_PREFLIGHT"

    source = r'''import ast,base64,hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);files=@@FILES@@
assert not code.exists()
code.mkdir(parents=True)
for name,body in files.items():
 path=code/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(body))
 if name.endswith('.py'):ast.parse(path.read_text(),filename=name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
print(json.dumps({'status':'STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS',
 'code':str(code),'manifest_sha256':sha(code/'code_manifest.json'),
 'config_sha256':sha(code/'score_config.json'),
 'source_hashes':{name:sha(code/name) for name in manifest},
 'target_labels_read':False}))
'''.replace("@@CODE@@", repr(config["code"])).replace(
        "@@FILES@@", repr(files)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["code_manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(prepared["score_config_sha256"]))
    stage = ssh("nsu-quadro", "python3 -", source)
    assert stage["status"] == "STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS"
    assert stage["manifest_sha256"] == prepared["code_manifest_sha256"]
    assert stage["config_sha256"] == prepared["score_config_sha256"]
    assert stage["source_hashes"] == manifest and stage["target_labels_read"] is False
    receipt = {"status": "STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS",
               "prepare_sha256": sha(PREPARE), "scale_audit_sha256": sha(SCALE_AUDIT),
               "preflight": preflight, "stage": stage, "target_labels_read": False,
               "scorer_launched": False, "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "manifest_sha256": stage["manifest_sha256"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
