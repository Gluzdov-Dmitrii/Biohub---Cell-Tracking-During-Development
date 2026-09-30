"""Freeze and stage the first reciprocal source6bba scratch training block."""
import base64
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from run_exp236_source_block01 import SOURCE_BUNDLE, SOURCE_BUNDLE_SHA, validate


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
DATA = REMOTE + "/data/exp213_source_view_20260912"
CODE = REMOTE + "/code/exp236_horaz_source6bba_block01_20260927"
RUN = REMOTE + "/runs/exp236_horaz_source6bba_block01_20260927"
WORK = ROOT / "work/exp236_source6bba_20260927"


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    assert not WORK.exists()
    assert not (ROOT / "reports/exp236_source_block01_prepare_20260927.json").exists()
    preflight = '''import hashlib,json,pathlib
bundle=pathlib.Path(BUNDLE);data=pathlib.Path(DATA)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(bundle)==BUNDLE_SHA
assert not pathlib.Path(CODE).exists() and not pathlib.Path(RUN).exists()
obj=json.loads(bundle.read_text());train=obj['source_train_movies'];inner=obj['source_validation_movies']
ids=train+inner
assert len(train)==115 and len(inner)==11 and len(set(ids))==126
assert all(name.startswith('6bba_') for name in ids)
assert all((data/(name+s)).exists() for name in ids for s in ('.zarr','.geff'))
print(json.dumps({'status':'PASS_EXP236_SOURCE6BBA_PREFLIGHT',
 'bundle_sha256':sha(bundle),'training_plan_sha256':obj['training_plan_sha256'],
 'train':train,'inner_validation':inner}))
'''.replace("BUNDLE_SHA", repr(SOURCE_BUNDLE_SHA)).replace("BUNDLE", repr(SOURCE_BUNDLE)).replace(
        "DATA", repr(DATA)).replace("CODE", repr(CODE)).replace("RUN", repr(RUN))
    source = ssh("nsu-a100", "python3 -", preflight)
    assert source["status"] == "PASS_EXP236_SOURCE6BBA_PREFLIGHT"
    assert source["bundle_sha256"] == SOURCE_BUNDLE_SHA
    record = lambda name: {"dataset_id": name,
                           "zarr_path": DATA + "/" + name + ".zarr",
                           "geff_path": DATA + "/" + name + ".geff"}
    manifest = {"source_embryo": "6bba", "target_embryo": "44b6",
                "rule": "EXP234_pinned_source6bba_partition_reused_without_target_labels",
                "source_bundle_sha256": SOURCE_BUNDLE_SHA,
                "training_plan_sha256": source["training_plan_sha256"],
                "train": [record(name) for name in source["train"]],
                "inner_validation": [record(name) for name in source["inner_validation"]]}
    manifest_body = (json.dumps(manifest, indent=2) + "\n").encode()
    plan = {"experiment": "EXP236", "purpose": "source_only_reciprocal_horaz_block01",
            "source_embryo": "6bba", "target_embryo": "44b6", "fold": 0,
            "block_end_epoch": 3, "planned_epochs": 50, "resume": False,
            "checkpoint_selection": "deferred_source_graph_10_20_30_40_50",
            "source_bundle_sha256": SOURCE_BUNDLE_SHA,
            "source_manifest_sha256": sha_bytes(manifest_body),
            "train": manifest["train"], "inner_validation": manifest["inner_validation"],
            "data_root": DATA, "output": RUN + "/output"}
    validate(plan)
    plan_body = (json.dumps(plan, indent=2) + "\n").encode()
    package = ROOT / "outputs/research/exp223_horaz0_package_20260921"
    files = {}
    for name, digest in json.loads((package / "package_manifest.json").read_text()).items():
        if name.startswith("selected/") and (name.endswith(".py") or name == "selected/resolved_config.json"):
            body = (package / name).read_bytes()
            assert sha_bytes(body) == digest
            files["horaz/" + name.removeprefix("selected/")] = body
    for name in ("run_exp236_source_block01.py", "run_exp226_source_pilot.py",
                 "exp226_protocol.py", "exp223_supervisor.py", "monitor_exp213_job.py"):
        files[name] = (ROOT / "scripts" / name).read_bytes()
    wrapper = (ROOT / "scripts/exp214_inference_job.py").read_text()
    old = "assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
    assert wrapper.count(old) == 1
    files["exp227_job.py"] = wrapper.replace(
        old, "assert config['script'] == 'run_exp236_source_block01.py'").encode()
    files["source6bba_manifest.json"] = manifest_body
    files["plan.json"] = plan_body
    hashes = {name: sha_bytes(body) for name, body in sorted(files.items())}
    files["code_manifest.json"] = json.dumps(hashes, indent=2).encode()
    stage = '''import ast,base64,hashlib,json,pathlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir()
for name,value in FILES.items():
 path=code/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(value))
 if name.endswith('.py'):ast.parse(path.read_text(),filename=str(path))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
print(json.dumps({'status':'STAGED_EXP236_SOURCE6BBA_BLOCK01',
 'code':str(code),'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'source_manifest_sha256':sha(code/'source6bba_manifest.json')}))
'''.replace("CODE", repr(CODE)).replace(
        "FILES", repr({name: base64.b64encode(body).decode() for name, body in files.items()}))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP236_SOURCE6BBA_BLOCK01"
    assert staged["manifest_sha256"] == sha_bytes(files["code_manifest.json"])
    assert staged["plan_sha256"] == sha_bytes(plan_body)
    assert staged["source_manifest_sha256"] == sha_bytes(manifest_body)

    WORK.mkdir(parents=True)
    (WORK / "source6bba_manifest.json").write_bytes(manifest_body)
    (WORK / "plan.json").write_bytes(plan_body)
    (WORK / "code_manifest.json").write_bytes(files["code_manifest.json"])
    config = {"experiment": "EXP236",
              "lease_id": "exp236-horaz-source6bba-block01-20260927",
              "token": "exp236_horaz_source6bba_block01_20260927",
              "code": CODE, "run": RUN, "max_seconds": 10800,
              "cpu_affinity": "0-7", "script": "run_exp236_source_block01.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    (ROOT / "reports/exp236_source_block01_config_20260927.json").write_text(
        json.dumps(config, indent=2) + "\n")
    receipt = {"status": "PREPARED_EXP236_SOURCE6BBA_BLOCK01_NO_TARGET_ACCESS",
               "preflight": {key: source[key] for key in ("status", "bundle_sha256", "training_plan_sha256")},
               "stage": staged, "train_movies": 115, "inner_validation_movies": 11,
               "target_data_opened": False}
    (ROOT / "reports/exp236_source_block01_prepare_20260927.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "plan_sha256": staged["plan_sha256"]}))


if __name__ == "__main__":
    main()
