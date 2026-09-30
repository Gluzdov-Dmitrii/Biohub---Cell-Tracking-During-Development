"""Guarded one-shot stage for one EXP236 target44b6 image-only chunk."""
import ast
import json

from monitor_exp213_job import ssh
from prepare_exp236_target_chunk_local import (
    ASSIGNMENT_SHA, CHECKPOINT, CHECKPOINT_SHA, HANDOFF, HANDOFF_SHA, PREREG,
    PREREG_SHA, ROOT, SCORE, SCORE_SHA, SOURCE_GRAPH_CODE, SOURCE_MANIFEST_SHA,
    SOURCE_PLAN, SOURCE_PLAN_SHA, TRAINING, TRAINING_SHA, paths, sha,
    validate_assignment, validate_source,
)


def stage_paths(index):
    prefix = f"exp236_target44b6_chunk{index:02d}"
    return {"stage": ROOT / f"reports/{prefix}_stage_20260927.json",
            "config": ROOT / f"reports/{prefix}_config_20260927.json"}


def local_gate(index):
    destination = paths(index)
    output = stage_paths(index)
    assert not output["stage"].exists() and not output["config"].exists()
    prepared = json.loads(destination["receipt"].read_text())
    assert prepared["status"] == "PREPARED_EXP236_TARGET44B6_CHUNK_LOCAL_ONLY"
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
    pinned = (("assignment.json", ASSIGNMENT_SHA), ("source_training.json", TRAINING_SHA),
              ("source_handoff.json", HANDOFF_SHA), ("source_score.json", SCORE_SHA),
              ("source_graph_plan.json", SOURCE_PLAN_SHA))
    for name, digest in pinned:
        assert manifest[name] == digest
    for source, digest in ((PREREG, PREREG_SHA), (TRAINING, TRAINING_SHA),
                           (HANDOFF, HANDOFF_SHA), (SCORE, SCORE_SHA),
                           (SOURCE_PLAN, SOURCE_PLAN_SHA)):
        assert sha(source) == digest
    assert prepared["prereg_sha256"] == PREREG_SHA
    training = json.loads((bundle / "source_training.json").read_text())
    handoff = json.loads((bundle / "source_handoff.json").read_text())
    score = json.loads((bundle / "source_score.json").read_text())
    source_plan = json.loads((bundle / "source_graph_plan.json").read_text())
    validate_source(training, handoff, score, source_plan)
    assignment = json.loads((bundle / "assignment.json").read_text())
    movies = validate_assignment(assignment, index)
    plan = json.loads((bundle / "plan.json").read_text())
    assert plan["experiment"] == "EXP236_TARGET44B6_CHUNK"
    assert plan["chunk_index"] == index and plan["chunk_count"] == 4
    assert plan["movies"] == prepared["movies"] == movies
    assert plan["code"] == destination["code"] and plan["output"] == destination["run"] + "/output"
    assert plan["assignment_sha256"] == ASSIGNMENT_SHA
    for key, digest in (("source_training_sha256", TRAINING_SHA),
                        ("source_handoff_sha256", HANDOFF_SHA),
                        ("source_score_sha256", SCORE_SHA),
                        ("source_graph_plan_sha256", SOURCE_PLAN_SHA)):
        assert plan[key] == prepared[key] == digest
    assert plan["checkpoint_epoch"] == prepared["checkpoint_epoch"] == 10
    assert plan["checkpoint"] == CHECKPOINT
    assert plan["checkpoint_sha256"] == prepared["checkpoint_sha256"] == CHECKPOINT_SHA
    recipe = json.loads((bundle / "stage_recipe.json").read_text())
    assert recipe["status"] == "LOCAL_ONLY_STAGE_RECIPE_NOT_EXECUTED"
    assert recipe["copy_parent_code"] == SOURCE_GRAPH_CODE
    assert recipe["parent_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert recipe["parent_plan_sha256"] == SOURCE_PLAN_SHA
    assert recipe["checkpoint"] == CHECKPOINT and recipe["checkpoint_sha256"] == CHECKPOINT_SHA
    assert recipe["target_code"] == destination["code"] and recipe["target_run"] == destination["run"]
    assert recipe["overlay_files"] == sorted(set(manifest) - {"stage_recipe.json"})
    assert recipe["wrapper_old_assertion"] == "assert config['script'] == 'run_exp236_source_graph10_v2.py'"
    assert recipe["wrapper_new_assertion"] == "assert config['script'] == 'run_exp236_target_chunk.py'"
    return prepared, plan, recipe, manifest


def remote_preflight_source(destination, recipe):
    return '''import hashlib,json,pathlib
source=pathlib.Path(@@SOURCE@@);target=pathlib.Path(@@TARGET@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists() and not run.exists()
assert sha(source/'code_manifest.json')==@@PARENT_MANIFEST_SHA@@
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 p=(source/name).resolve();assert p.is_relative_to(source.resolve()) and sha(p)==digest,name
assert sha(source/'plan.json')==@@PARENT_PLAN_SHA@@
assert sha(pathlib.Path(@@CHECKPOINT@@))==@@CHECKPOINT_SHA@@
print(json.dumps({'status':'PASS_EXP236_TARGET_STAGE_PARENT_PREFLIGHT',
 'parent_manifest_sha256':sha(source/'code_manifest.json'),
 'parent_plan_sha256':sha(source/'plan.json'),
 'checkpoint_sha256':sha(pathlib.Path(@@CHECKPOINT@@))}))
'''.replace("@@SOURCE@@", repr(recipe["copy_parent_code"])).replace(
        "@@TARGET@@", repr(destination["code"])).replace("@@RUN@@", repr(destination["run"])).replace(
        "@@PARENT_MANIFEST_SHA@@", repr(recipe["parent_manifest_sha256"])).replace(
        "@@PARENT_PLAN_SHA@@", repr(recipe["parent_plan_sha256"])).replace(
        "@@CHECKPOINT@@", repr(recipe["checkpoint"])).replace(
        "@@CHECKPOINT_SHA@@", repr(recipe["checkpoint_sha256"]))


def remote_stage_source(destination, recipe, manifest, files):
    return '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(@@SOURCE@@);target=pathlib.Path(@@TARGET@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists() and not run.exists()
assert sha(source/'code_manifest.json')==@@PARENT_MANIFEST_SHA@@
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 p=(source/name).resolve();assert p.is_relative_to(source.resolve()) and sha(p)==digest,name
assert sha(source/'plan.json')==@@PARENT_PLAN_SHA@@
assert sha(pathlib.Path(@@CHECKPOINT@@))==@@CHECKPOINT_SHA@@
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
staged={path.relative_to(target).as_posix():sha(path)
        for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(staged,indent=2)+'\\n')
assert sha(target/'plan.json')==expected['plan.json']
assert sha(target/'source_handoff.json')==expected['source_handoff.json']
assert sha(target/'source_graph_plan.json')==expected['source_graph_plan.json']
assert sha(target/'assignment.json')==expected['assignment.json']
print(json.dumps({'status':'STAGED_EXP236_TARGET44B6_CHUNK_NO_LABELS','code':str(target),
 'run':str(run),'manifest_sha256':sha(target/'code_manifest.json'),
 'plan_sha256':sha(target/'plan.json'),'runner_sha256':sha(target/'run_exp236_target_chunk.py'),
 'source_handoff_sha256':sha(target/'source_handoff.json'),
 'source_graph_plan_sha256':sha(target/'source_graph_plan.json'),
 'assignment_sha256':sha(target/'assignment.json')}))
'''.replace("@@SOURCE@@", repr(recipe["copy_parent_code"])).replace(
        "@@TARGET@@", repr(destination["code"])).replace("@@RUN@@", repr(destination["run"])).replace(
        "@@PARENT_MANIFEST_SHA@@", repr(recipe["parent_manifest_sha256"])).replace(
        "@@PARENT_PLAN_SHA@@", repr(recipe["parent_plan_sha256"])).replace(
        "@@CHECKPOINT@@", repr(recipe["checkpoint"])).replace(
        "@@CHECKPOINT_SHA@@", repr(recipe["checkpoint_sha256"])).replace(
        "@@OLD_ASSERTION@@", repr(recipe["wrapper_old_assertion"])).replace(
        "@@NEW_ASSERTION@@", repr(recipe["wrapper_new_assertion"])).replace(
        "@@FILES@@", repr(files)).replace("@@TRANSFER_MANIFEST@@", repr(manifest))


def stage_index(index):
    destination = paths(index)
    output = stage_paths(index)
    prepared, plan, recipe, manifest = local_gate(index)
    parent = ssh("nsu-a100", "python3 -", remote_preflight_source(destination, recipe))
    assert parent == {"status": "PASS_EXP236_TARGET_STAGE_PARENT_PREFLIGHT",
                      "parent_manifest_sha256": SOURCE_MANIFEST_SHA,
                      "parent_plan_sha256": SOURCE_PLAN_SHA,
                      "checkpoint_sha256": CHECKPOINT_SHA}
    files = {name: (destination["bundle"] / name).read_bytes()
             for name in recipe["overlay_files"]}
    transfer_manifest = {name: manifest[name] for name in recipe["overlay_files"]}
    staged = ssh("nsu-a100", "python3 -",
                 remote_stage_source(destination, recipe, transfer_manifest, files))
    assert staged["status"] == "STAGED_EXP236_TARGET44B6_CHUNK_NO_LABELS"
    assert staged["code"] == destination["code"] and staged["run"] == destination["run"]
    assert staged["plan_sha256"] == manifest["plan.json"]
    assert staged["runner_sha256"] == manifest["run_exp236_target_chunk.py"]
    assert staged["source_handoff_sha256"] == HANDOFF_SHA
    assert staged["source_graph_plan_sha256"] == SOURCE_PLAN_SHA
    assert staged["assignment_sha256"] == ASSIGNMENT_SHA
    config = {"experiment": "EXP236_TARGET44B6_CHUNK", "chunk_index": index,
              "lease_id": destination["lease_id"], "token": destination["token"],
              "pool": "a100", "code": destination["code"], "run": destination["run"],
              "max_seconds": 10800, "cpu_affinity": "0-7",
              "resources": {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4},
              "script": "run_exp236_target_chunk.py",
              "arguments": [destination["code"] + "/plan.json", "--plan-sha256",
                            staged["plan_sha256"]]}
    receipt = {"status": "STAGED_EXP236_TARGET44B6_CHUNK_NO_LABELS",
               "chunk_index": index, "code": destination["code"], "run": destination["run"],
               "lease_id": destination["lease_id"],
               "manifest_sha256": staged["manifest_sha256"],
               "plan_sha256": staged["plan_sha256"],
               "source_handoff_sha256": HANDOFF_SHA,
               "checkpoint_sha256": CHECKPOINT_SHA,
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
