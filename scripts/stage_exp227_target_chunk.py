"""Stage one immutable EXP227 target chunk from a sealed local transfer bundle.

Staging copies source-only graph code and overlays the image-only runner. It
never launches a worker, claims a GPU, or opens target labels.
"""
import ast
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from prepare_exp227_target_chunk0_local import (
    ASSIGNMENT_SHA, PREREG, ROOT, SELECTION, paths, sha, validate_assignment,
    validate_selection,
)


def stage_paths(index):
    prefix = f"exp227_target6bba_chunk{index:02d}"
    return {"stage": ROOT / f"reports/{prefix}_stage_20260927.json",
            "config": ROOT / f"reports/{prefix}_config_20260927.json"}


def local_gate(index):
    destination = paths(index)
    output = stage_paths(index)
    assert not output["stage"].exists() and not output["config"].exists()
    prepared = json.loads(destination["receipt"].read_text())
    assert prepared["status"] == "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY"
    assert prepared["chunk_index"] == index and prepared["bundle"] == str(destination["bundle"])
    assert prepared["code"] == destination["code"] and prepared["run"] == destination["run"]
    assert prepared["lease_id"] == destination["lease_id"]
    assert prepared["remote_stage_created"] is False and prepared["remote_run_created"] is False
    assert prepared["gpu_claimed"] is False and prepared["target_labels_read"] is False
    bundle = destination["bundle"]
    manifest_path = bundle / "local_bundle_manifest.json"
    assert sha(manifest_path) == prepared["bundle_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    assert set(p.name for p in bundle.iterdir()) == set(manifest) | {"local_bundle_manifest.json"}
    for name, digest in manifest.items():
        item = (bundle / name).resolve()
        assert item.is_relative_to(bundle.resolve()) and sha(item) == digest, name
        if name.endswith(".py"):
            ast.parse(item.read_text(), filename=name)
    assert manifest["plan.json"] == prepared["plan_sha256"]
    assert manifest["selection.json"] == prepared["selection_sha256"]
    assert manifest["assignment.json"] == prepared["assignment_sha256"] == ASSIGNMENT_SHA
    assert sha(PREREG) == prepared["prereg_sha256"]
    assert sha(SELECTION) == prepared["selection_sha256"]
    selection = json.loads((bundle / "selection.json").read_text())
    chosen = validate_selection(selection, prepared["prereg_sha256"])
    assignment = json.loads((bundle / "assignment.json").read_text())
    movies = validate_assignment(assignment, index)
    plan = json.loads((bundle / "plan.json").read_text())
    assert plan["experiment"] == "EXP227_TARGET6BBA_CHUNK"
    assert plan["chunk_index"] == index and plan["chunk_count"] == 8
    assert plan["movies"] == prepared["movies"] == movies
    assert plan["code"] == destination["code"] and plan["output"] == destination["run"] + "/output"
    assert plan["assignment_sha256"] == ASSIGNMENT_SHA
    assert plan["selection_sha256"] == prepared["selection_sha256"]
    assert plan["checkpoint_epoch"] == selection["selected_epoch"]
    assert plan["checkpoint"] == selection["checkpoint"]
    assert plan["checkpoint_sha256"] == prepared["checkpoint_sha256"] == selection["checkpoint_sha256"]
    recipe = json.loads((bundle / "stage_recipe.json").read_text())
    assert recipe["status"] == "LOCAL_ONLY_STAGE_RECIPE_NOT_EXECUTED"
    assert recipe["copy_parent_code"] == chosen["graph_code"]
    assert recipe["parent_manifest_sha256"] == chosen["graph_manifest_sha256"]
    assert recipe["target_code"] == destination["code"] and recipe["target_run"] == destination["run"]
    assert recipe["overlay_files"] == sorted(set(manifest) - {"stage_recipe.json"})
    assert recipe["wrapper_old_assertion"] == (
        f"assert config['script'] == 'run_exp227_source_graph{selection['selected_epoch']}.py'")
    return prepared, selection, chosen, plan, recipe, manifest


def remote_preflight_source(destination, chosen):
    return '''import hashlib,json,pathlib
source=pathlib.Path(@@SOURCE@@);target=pathlib.Path(@@TARGET@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists() and not run.exists()
assert sha(source/'code_manifest.json')==@@PARENT_MANIFEST_SHA@@
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 p=(source/name).resolve();assert p.is_relative_to(source.resolve()) and sha(p)==digest,name
assert sha(pathlib.Path(@@CHECKPOINT@@))==@@CHECKPOINT_SHA@@
print(json.dumps({'status':'PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT',
                  'parent_manifest_sha256':sha(source/'code_manifest.json'),
                  'checkpoint_sha256':sha(pathlib.Path(@@CHECKPOINT@@))}))
'''.replace("@@SOURCE@@", repr(chosen["graph_code"])).replace(
        "@@TARGET@@", repr(destination["code"])).replace("@@RUN@@", repr(destination["run"])).replace(
        "@@PARENT_MANIFEST_SHA@@", repr(chosen["graph_manifest_sha256"])).replace(
        "@@CHECKPOINT_SHA@@", repr(chosen["checkpoint_sha256"])).replace(
        "@@CHECKPOINT@@", repr(chosen["checkpoint"]))


def remote_stage_source(destination, recipe, manifest, files):
    return '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(@@SOURCE@@);target=pathlib.Path(@@TARGET@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists() and not run.exists()
assert sha(source/'code_manifest.json')==@@PARENT_MANIFEST_SHA@@
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 p=(source/name).resolve();assert p.is_relative_to(source.resolve()) and sha(p)==digest,name
shutil.copytree(source,target)
wrapper=target/'exp227_job.py';body=wrapper.read_text();old=@@OLD_ASSERTION@@;new=@@NEW_ASSERTION@@
assert body.count(old)==1
wrapper.write_text(body.replace(old,new))
files=@@FILES@@;expected=@@TRANSFER_MANIFEST@@
assert set(files)==set(expected)
for name,contents in files.items():
 assert hashlib.sha256(contents).hexdigest()==expected[name],name
 path=(target/name).resolve();assert path.is_relative_to(target.resolve())
 path.write_bytes(contents)
 if name.endswith('.py'):ast.parse(contents.decode('utf-8'),filename=name)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
staged={str(path.relative_to(target)).replace('\\\\','/'):sha(path)
        for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(staged,indent=2)+'\\n')
assert sha(target/'plan.json')==expected['plan.json']
assert sha(target/'selection.json')==expected['selection.json']
assert sha(target/'assignment.json')==expected['assignment.json']
print(json.dumps({'status':'STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS','code':str(target),
 'run':str(run),'manifest_sha256':sha(target/'code_manifest.json'),
 'plan_sha256':sha(target/'plan.json'),'runner_sha256':sha(target/'run_exp227_target_chunk.py'),
 'selection_sha256':sha(target/'selection.json'),'assignment_sha256':sha(target/'assignment.json')}))
'''.replace("@@SOURCE@@", repr(recipe["copy_parent_code"])).replace(
        "@@TARGET@@", repr(destination["code"])).replace("@@RUN@@", repr(destination["run"])).replace(
        "@@PARENT_MANIFEST_SHA@@", repr(recipe["parent_manifest_sha256"])).replace(
        "@@OLD_ASSERTION@@", repr(recipe["wrapper_old_assertion"])).replace(
        "@@NEW_ASSERTION@@", repr(recipe["wrapper_new_assertion"])).replace(
        "@@FILES@@", repr(files)).replace("@@TRANSFER_MANIFEST@@", repr(manifest))


def stage_index(index):
    destination = paths(index)
    output = stage_paths(index)
    prepared, selection, chosen, plan, recipe, manifest = local_gate(index)
    parent = ssh("nsu-a100", "python3 -", remote_preflight_source(destination, chosen))
    assert parent["status"] == "PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT"
    assert parent["parent_manifest_sha256"] == chosen["graph_manifest_sha256"]
    assert parent["checkpoint_sha256"] == chosen["checkpoint_sha256"]
    files = {name: (destination["bundle"] / name).read_bytes()
             for name in recipe["overlay_files"]}
    transfer_manifest = {name: manifest[name] for name in recipe["overlay_files"]}
    staged = ssh("nsu-a100", "python3 -",
                 remote_stage_source(destination, recipe, transfer_manifest, files))
    assert staged["status"] == "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS"
    assert staged["code"] == destination["code"] and staged["run"] == destination["run"]
    assert staged["plan_sha256"] == manifest["plan.json"]
    assert staged["runner_sha256"] == manifest["run_exp227_target_chunk.py"]
    assert staged["selection_sha256"] == manifest["selection.json"]
    assert staged["assignment_sha256"] == ASSIGNMENT_SHA
    config = {"experiment": "EXP227_TARGET6BBA_CHUNK", "chunk_index": index,
              "lease_id": destination["lease_id"], "token": destination["token"],
              "pool": "a100", "code": destination["code"], "run": destination["run"],
              "max_seconds": 10800, "cpu_affinity": "0-7",
              "resources": {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4},
              "script": "run_exp227_target_chunk.py",
              "arguments": [destination["code"] + "/plan.json", "--plan-sha256",
                            staged["plan_sha256"]]}
    receipt = {"status": "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS",
               "chunk_index": index, "code": destination["code"], "run": destination["run"],
               "lease_id": destination["lease_id"],
               "manifest_sha256": staged["manifest_sha256"],
               "plan_sha256": staged["plan_sha256"],
               "selection_sha256": staged["selection_sha256"],
               "checkpoint_sha256": plan["checkpoint_sha256"],
               "movies": plan["movies"], "parent": parent, "staged": staged,
               "local_prepare_sha256": sha(destination["receipt"]),
               "local_bundle_manifest_sha256": prepared["bundle_manifest_sha256"],
               "remote_run_created": False, "gpu_claimed": False, "target_labels_read": False}
    output["config"].write_text(json.dumps(config, indent=2) + "\n")
    output["stage"].write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "chunk_index": index,
                      "manifest_sha256": receipt["manifest_sha256"]}))
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    stage_index(parser.parse_args().index)
