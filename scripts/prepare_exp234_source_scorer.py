"""Stage immutable official source scorer; this does not open labels."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp234_source_scorer_v3_20260926"
INFERENCE = REMOTE + "/code/exp234_source_threshold_v2_20260926"


def main():
    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp234_source_threshold.py", "score_exp214_paired.py",
        "score_exp223_official.py", "exp234_source_scope.py")}
    files["exp223_config.json"] = (ROOT / "reports/exp223_official_score_config_v2_20260922.json").read_text()
    source_receipt = json.loads((ROOT / "reports/exp234_source_prepare_v2_20260926.json").read_text())
    configs = {}
    for embryo in ("44b6", "6bba"):
        job = json.loads((ROOT / ("reports/exp234_source_" + embryo + "_config_v2_20260926.json")).read_text())
        assert job["experiment"] == "EXP234" and job["arguments"][1] == "--plan-sha256"
        config = {"experiment": "EXP234_SOURCE_SCORER", "source_embryo": embryo,
                  "inference_code": INFERENCE,
                  "inference_manifest_sha256": source_receipt["staging"]["manifest_sha256"],
                  "plan_sha256": job["arguments"][2],
                  "run": job["run"], "output": job["run"] + "/score",
                  "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
                  "data_dir": REMOTE + "/data/exp213_source_view_20260912",
                  "exp223_config": CODE + "/exp223_config.json",
                  "exp223_config_sha256": hashlib.sha256(files["exp223_config.json"].encode()).hexdigest(),
                  "expected_movies": source_receipt["selection"][embryo]["movies"],
                  "expected_model_shas": {role: source_receipt["selection"][embryo]["weights"][role]["sha256"]
                                          for role in ("primary", "secondary", "center")},
                  "selection_rule": "maximum_official_source_score_tie_baseline_0965"}
        name = embryo + "_score_config.json"
        files[name] = json.dumps(config, indent=2) + "\n"
        configs[embryo] = {"path": CODE + "/" + name,
                           "sha256": hashlib.sha256(files[name].encode()).hexdigest(),
                           "run": job["run"]}
    source = '''import ast,hashlib,json,pathlib
p=pathlib.Path(CODE);assert not p.exists();p.mkdir(parents=True)
for name,body in FILES.items():
 q=p/name;q.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
manifest={name:sha(p/name) for name in sorted(FILES)}
(p/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'code':str(p),'files':len(manifest),'manifest_sha256':sha(p/'code_manifest.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-a100", "python3 -", source)
    receipt = {"status": "PREPARED_EXP234_SOURCE_SCORER", "staging": staged,
               "configs": configs, "no_labels_opened": True}
    (ROOT / "reports/exp234_source_scorer_prepare_v3_20260926.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"]}))


if __name__ == "__main__":
    main()
