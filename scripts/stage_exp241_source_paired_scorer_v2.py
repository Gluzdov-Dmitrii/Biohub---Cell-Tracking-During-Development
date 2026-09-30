"""One-shot EXP241 scorer stage. Default is local review; --execute mutates remote code only."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh


if not __debug__:
    raise RuntimeError("EXP241 stage requires assertions")

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp241_source_paired_scorer_v2_20260927"
MANIFEST = BUNDLE / "manifest.json"
MANIFEST_SHA = "ed8c7ac72c5a3f73d30570d24133f4aff7124b4e7dbf52d9e0a6cfe098424ce1"
CONFIG_SHA = "251062a7bbccb65d2219d78ede6d09bb617088d79905b02edd53fb06aea6685c"
GRAPH_RECEIPT_SHA = "90d0b3882cdcb53092bdce37f1dd619e3566e5cbd8f1b7e6dbcc4c630947cad4"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp241_source_paired_scorer_v2_20260927"
RUN = REMOTE + "/runs/exp241_source_paired_scorer_v2_20260927"
GRAPH_RUN = REMOTE + "/runs/exp241_fixed_two_peak_source_candidate_v1_20260927"
PYTHON = REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python"
INTENT = ROOT / "reports/exp241_source_paired_scorer_v2_stage_intent_20260927.json"
RECEIPT = ROOT / "reports/exp241_source_paired_scorer_v2_stage_20260927.json"
V1_FAILURE = ROOT / "reports/exp241_source_paired_scorer_v1_failure_reconciled_20260927.json"
V1_FAILURE_SHA = "8cf1410b6f175b42c97344ad125713136577e68d9e3a84a9a56840333b2deb76"
PRIOR_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
PRIOR_GATE_SHA = "735496f5cf6dca2e24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_json(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def failure_gate() -> dict:
    assert sha(V1_FAILURE) == V1_FAILURE_SHA
    record = json.loads(V1_FAILURE.read_text())
    assert record["status"] == "PASS_EXP241_V1_FAILURE_RECONCILED_BEFORE_GEFF"
    remote = record["remote"]
    assert remote["status"] == record["status"]
    assert remote["prior_result_sha256"] == PRIOR_RESULT_SHA
    assert remote["prior_gate_actual_sha256"] == PRIOR_GATE_SHA
    assert remote["source_geff_reached"] is False
    assert remote["candidate_metric_reached"] is False
    assert remote["child_absent"] is True and remote["timeout"] is False
    assert remote["output_files"].keys() == {"no_label_gate.json"}
    assert record["source_geff_read_by_reconciler"] is False
    return record


def local_bundle() -> tuple[dict, dict]:
    assert sha(MANIFEST) == MANIFEST_SHA
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["status"] == "SEALED_EXP241_SOURCE_PAIRED_SCORER_V2"
    assert len(manifest["files"]) == 12
    files = {path.relative_to(BUNDLE).as_posix() for path in BUNDLE.rglob("*") if path.is_file()}
    assert files == set(manifest["files"]) | {"manifest.json"}
    for name, digest in manifest["files"].items():
        path = (BUNDLE / name).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and sha(path) == digest, name
    assert sha(BUNDLE / "config.json") == CONFIG_SHA
    config = json.loads((BUNDLE / "config.json").read_text())
    assert config["status"] == "SEALED_EXP241_SOURCE_PAIRED_SCORER_V2"
    assert config["source_only"] and config["labels_read_at_prepare"] is False
    assert config["target_data_opened"] is False and config["gpu_used"] is False
    assert config["kaggle_post"] is False
    assert config["output"] == RUN + "/output" and config["graph_run"] == GRAPH_RUN
    assert config["graph_verified_receipt_sha256"] == GRAPH_RECEIPT_SHA
    graph = json.loads((BUNDLE / "graph_verified.json").read_text())
    assert graph["status"] == "PASS_EXP241_INDEPENDENT_LABEL_FREE_GRAPH_VERIFICATION"
    assert graph["run"] == GRAPH_RUN and graph["remote"]["run"] == GRAPH_RUN
    assert graph["remote"]["result_sha256"] == config["graph_result_sha256"]
    assert graph["remote"]["no_label_gate_sha256"] == config["graph_no_label_gate_sha256"]
    assert graph["remote"]["selected_chains"] == {"source44": 835, "source6": 358}
    assert not any(graph[k] for k in ("source_labels_read", "target_data_opened",
                                       "metric_computed", "gpu_used", "kaggle_post"))
    return manifest, config


def render(source: str, values: dict[str, object]) -> str:
    for key, value in values.items():
        assert key in source
        source = source.replace(key, repr(value))
    assert "@@" not in source
    compile(source, "exp241_remote_stage_template", "exec")
    return source


def remote_preflight_source(expect_code: bool) -> str:
    source = r'''import hashlib,json,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP241 remote stage requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@);graph=pathlib.Path(@@GRAPH_RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP241 stage preflight denies all GEFF')
sys.addaudithook(deny)
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert code.exists()==@@EXPECT_CODE@@ and not run.exists()
assert sha(graph/'output/result.json')==@@GRAPH_RESULT_SHA@@
assert sha(graph/'output/no_label_gate.json')==@@GRAPH_GATE_SHA@@
if @@EXPECT_CODE@@:
 assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
 manifest=json.loads((code/'manifest.json').read_text())
 observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
 assert observed=={**manifest['files'],'manifest.json':@@MANIFEST_SHA@@}
print(json.dumps({'status':'PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS',
 'code_present':@@EXPECT_CODE@@,'run_absent':True,
 'graph_result_sha256':@@GRAPH_RESULT_SHA@@,
 'source_labels_read':False,'target_data_opened':False}))
'''
    config = json.loads((BUNDLE / "config.json").read_text())
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN, "@@GRAPH_RUN@@": GRAPH_RUN,
                           "@@EXPECT_CODE@@": expect_code,
                           "@@GRAPH_RESULT_SHA@@": config["graph_result_sha256"],
                           "@@GRAPH_GATE_SHA@@": config["graph_no_label_gate_sha256"],
                           "@@MANIFEST_SHA@@": MANIFEST_SHA})


def remote_stage_source(manifest: dict) -> str:
    payload = {name: base64.b64encode((BUNDLE / name).read_bytes()).decode("ascii")
               for name in [*manifest["files"], "manifest.json"]}
    expected = {**manifest["files"], "manifest.json": MANIFEST_SHA}
    source = r'''import ast,base64,hashlib,json,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP241 remote stage requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@);graph=pathlib.Path(@@GRAPH_RUN@@)
payload=@@PAYLOAD@@;expected=@@EXPECTED@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP241 stage denies all GEFF')
sys.addaudithook(deny)
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert not code.exists() and not run.exists()
assert sha(graph/'output/result.json')==@@GRAPH_RESULT_SHA@@
assert sha(graph/'output/no_label_gate.json')==@@GRAPH_GATE_SHA@@
code.mkdir(parents=True,exist_ok=False)
for name,encoded in payload.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(encoded,validate=True))
 assert sha(path)==expected[name],name
 if name.endswith('.py'):ast.parse(path.read_text(),filename=name)
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
print(json.dumps({'status':'STAGED_EXP241_SOURCE_PAIRED_SCORER_NO_LABELS',
 'code':str(code),'manifest_sha256':sha(code/'manifest.json'),
 'file_hashes':observed,'run_absent':True,'source_labels_read':False,
 'target_data_opened':False,'gpu_used':False,'kaggle_post':False}))
'''
    config = json.loads((BUNDLE / "config.json").read_text())
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN, "@@GRAPH_RUN@@": GRAPH_RUN,
                           "@@PAYLOAD@@": payload, "@@EXPECTED@@": expected,
                           "@@GRAPH_RESULT_SHA@@": config["graph_result_sha256"],
                           "@@GRAPH_GATE_SHA@@": config["graph_no_label_gate_sha256"]})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest, config = local_bundle()
    if not args.execute:
        remote_preflight_source(False)
        remote_stage_source(manifest)
        remote_preflight_source(True)
        print(json.dumps({"status": "EXP241_SCORER_STAGE_LOCAL_REVIEW_ONLY",
                          "manifest_sha256": MANIFEST_SHA, "files": len(manifest["files"]),
                          "v1_failure_reconciled": V1_FAILURE.exists(),
                          "graph_verified_receipt_sha256": GRAPH_RECEIPT_SHA,
                          "remote_mutation": False, "source_labels_read": False}))
        return
    failure_gate()
    assert not INTENT.exists() and not RECEIPT.exists(), "Reconcile existing stage intent first"
    preflight = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                    remote_preflight_source(False))
    assert preflight["status"] == "PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS"
    exclusive_json(INTENT, {"status": "INTENT_EXP241_SCORER_STAGE",
                            "manifest_sha256": MANIFEST_SHA, "config_sha256": CONFIG_SHA,
                            "v1_failure_receipt_sha256": V1_FAILURE_SHA,
                            "graph_verified_receipt_sha256": GRAPH_RECEIPT_SHA,
                            "preflight": preflight, "source_labels_read": False})
    staged = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                 remote_stage_source(manifest))
    assert staged["status"] == "STAGED_EXP241_SOURCE_PAIRED_SCORER_NO_LABELS"
    assert staged["manifest_sha256"] == MANIFEST_SHA
    readback = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                   remote_preflight_source(True))
    assert readback["status"] == "PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS"
    exclusive_json(RECEIPT, {"status": staged["status"],
                             "manifest_sha256": MANIFEST_SHA,
                             "config_sha256": CONFIG_SHA,
                             "v1_failure_receipt_sha256": V1_FAILURE_SHA,
                             "graph_verified_receipt_sha256": GRAPH_RECEIPT_SHA,
                             "intent_sha256": sha(INTENT),
                             "preflight": preflight, "stage": staged, "readback": readback,
                             "run_started": False, "source_labels_read": False,
                             "target_data_opened": False, "gpu_used": False,
                             "kaggle_post": False})
    print(json.dumps({"status": staged["status"], "manifest_sha256": MANIFEST_SHA}))


if __name__ == "__main__":
    main()
