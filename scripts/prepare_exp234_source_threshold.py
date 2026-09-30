"""Freeze and stage source-only threshold arms for both clean EXP214 folds."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp234_source_threshold_v2_20260926"
THRESHOLDS = ["0.900", "0.940", "0.965"]
SOURCE_SHA = "5389953eb7c2f68b6e3664985ceb252d0eac391b65821b0ced692693003cbcba"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    plan = json.loads((ROOT / "reports/exp214_equal_time_plan_20260912.json").read_text())
    remote_source = '''import hashlib,json,pathlib
r=pathlib.Path(ROOT)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
training=json.loads((r/'code/exp214_strong60_v1_20260912/plan.json').read_text())
out={'folds':training['folds'],'notebook_sha256':sha(r/'code/exp214_inference_v7_20260912/compact47_v20.ipynb'),'embryos':{}}
for embryo in ('44b6','6bba'):
 b=json.loads((r/'code/exp214_eval90_inputs_20260913'/(embryo+'_bundle.json')).read_text())
 split=json.loads((r/'runs/exp180_reciprocal_deepcenter_training_20260910'/('trainer_'+embryo+'_source.json')).read_text())[0]
 model={}
 for role in ('primary','secondary','center'):
  item=b[role]; p=pathlib.Path(item['path']); assert sha(p)==item['sha256'],(embryo,role)
  model[role]={'sha256':sha(p)}
  if role!='center':
   status=p.parent/'status.json';assert sha(status)==item['source_status_sha256']
   s=json.loads(status.read_text()); assert s['best_sha256']==item['sha256'] and s['target_data_opened'] is False
   assert s['contract']['plan_sha256']==item['actual_training_plan_sha256']
 out['embryos'][embryo]={'bundle':b,'center_seen':sorted({n.removesuffix('.zarr') for part in ('train','test') for n in split[part]}),'model':model}
print(json.dumps(out))
'''.replace("ROOT", repr(REMOTE))
    remote = ssh("nsu-quadro", "python3 -", remote_source)
    assert remote["notebook_sha256"] == SOURCE_SHA
    assert {k: remote["folds"][k] for k in ("44b6", "6bba")} == {
        k: plan["folds"][k] for k in ("44b6", "6bba")}

    public = (ROOT / "scripts/run_exp214_public_fold.py").read_text()
    old = "        assert all(not name.startswith(bundle['source_embryo']+'_') for name in movies),'Target is source embryo'"
    assert public.count(old) == 1
    public = public.replace(old, "        from exp234_source_scope import validate_scope\n        validate_scope(bundle,movies)")
    assert public.count("import shutil\n") == 1
    public = public.replace("import shutil\n", "import shutil\nimport sys\n")
    marker = "    args.output.mkdir(parents=True,exist_ok=False)\n"
    assert public.count(marker) == 1
    public = public.replace(marker, marker + '''    from exp234_source_scope import reject_label_geff_open
    prediction_root = (args.output / 'tracking_repo' / 'predictions').resolve()
    sys.addaudithook(lambda event, values: reject_label_geff_open(event, values, prediction_root))
''')
    wrapper = (ROOT / "scripts/exp214_inference_job.py").read_text()
    old = "assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
    assert wrapper.count(old) == 1
    wrapper = wrapper.replace(old, "assert config['script'] == 'run_exp234_source_threshold.py'")
    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "exp234_source_scope.py", "run_exp234_source_threshold.py",
        "bound_exp214_submission.py", "exp223_supervisor.py", "monitor_exp213_job.py")}
    files.update({"run_exp214_public_fold.py": public, "exp214_inference_job.py": wrapper})

    configs = {}
    selection = {}
    for embryo in ("44b6", "6bba"):
        fold = plan["folds"][embryo]
        seen = set(remote["embryos"][embryo]["center_seen"])
        movies = sorted(set(fold["validation"]) - seen)
        assert len(movies) == (8 if embryo == "44b6" else 11)
        assert not set(movies).intersection(fold["train"])
        bundle = dict(remote["embryos"][embryo]["bundle"])
        bundle.update(evaluation_mode="EXP234_SOURCE_THRESHOLD_SELECTION",
                      source_validation_movies=movies,
                      source_train_movies=fold["train"],
                      center_seen_movies=sorted(seen),
                      selection_rule="maximum_official_source_score_tie_baseline_0965")
        run = REMOTE + "/runs/exp234_source_" + embryo + "_v2_20260926"
        movies_name = embryo + "_movies.json"
        bundle_name = embryo + "_bundle.json"
        plan_name = embryo + "_plan.json"
        files[movies_name] = json.dumps(movies, indent=2) + "\n"
        files[bundle_name] = json.dumps(bundle, indent=2) + "\n"
        job = {"experiment": "EXP234", "source_embryo": embryo,
               "thresholds": THRESHOLDS, "movie_count": len(movies),
               "code": CODE, "output": run + "/output",
               "notebook": REMOTE + "/code/exp214_inference_v7_20260912/compact47_v20.ipynb",
               "notebook_sha256": SOURCE_SHA,
               "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
               "data_dir": REMOTE + "/data/exp213_source_view_20260912",
               "movies": CODE + "/" + movies_name,
               "movies_sha256": sha_bytes(files[movies_name].encode()),
               "bundle": CODE + "/" + bundle_name,
               "bundle_sha256": sha_bytes(files[bundle_name].encode()),
               "selection_rule": "maximum_official_source_score_tie_baseline_0965",
               "labels_allowed_during_inference": False}
        files[plan_name] = json.dumps(job, indent=2) + "\n"
        configs[embryo] = {"experiment": "EXP234",
                           "lease_id": "exp234-source-" + embryo + "-v2-20260926",
                           "token": "exp234_source_" + embryo + "_v2_20260926",
                           "pool": "a100", "code": CODE, "run": run,
                           "max_seconds": 10800, "cpu_affinity": "0-7",
                           "script": "run_exp234_source_threshold.py",
                           "arguments": [CODE + "/" + plan_name, "--plan-sha256",
                                         sha_bytes(files[plan_name].encode())],
                           "resources": {"cpu": 8, "ram_gib": 64, "disk_growth_gib": 3}}
        selection[embryo] = {"movies": movies, "source_train_count": len(fold["train"]),
                             "center_seen_count": len(seen),
                             "center_excluded_from_validation": sorted(set(fold["validation"]) & seen),
                             "weights": remote["embryos"][embryo]["model"]}

    source = '''import hashlib,json,pathlib
p=pathlib.Path(CODE);assert not p.exists();p.mkdir(parents=True)
for name,body in FILES.items(): (p/name).write_text(body)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
manifest={name:sha(p/name) for name in sorted(FILES)}
(p/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'code':str(p),'file_count':len(manifest),'manifest_sha256':sha(p/'code_manifest.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-quadro", "python3 -", source)
    for embryo, config in configs.items():
        path = ROOT / ("reports/exp234_source_" + embryo + "_config_v2_20260926.json")
        path.write_text(json.dumps(config, indent=2) + "\n")
    receipt = {"status": "PREPARED_EXP234_SOURCE_ONLY", "experiment": "EXP234",
               "staging": staged, "selection": selection,
               "thresholds": THRESHOLDS, "notebook_sha256": SOURCE_SHA,
               "source_file_hashes": {k: sha_bytes(v.encode()) for k, v in files.items()}}
    (ROOT / "reports/exp234_source_prepare_v2_20260926.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "code": CODE,
                      "movies": {e: len(selection[e]["movies"]) for e in selection},
                      "manifest_sha256": staged["manifest_sha256"]}))


if __name__ == "__main__":
    main()
