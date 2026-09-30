"""Stage an immutable CPU scorer for the completed EXP228 fixed ensemble."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp228_official_scorer_v1_20260926"
INFERENCE = REMOTE + "/code/exp228_horaz_ensemble_quadro_v2_20260923"


def main():
    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp228_ensemble_official.py", "score_exp223_official.py", "score_exp214_paired.py")}
    original = ROOT / "reports/exp223_official_score_config_v2_20260922.json"
    files["exp223_config.json"] = original.read_text()
    staged = json.loads((ROOT / "work/horaz_parallel_20260923/ensemble_quadro_staging.json").read_text())
    assert staged["code"] == INFERENCE
    config = {"experiment": "EXP228_OFFICIAL_SCORE175",
              "inference_code": INFERENCE,
              "inference_manifest_sha256": staged["code_manifest_sha256"],
              "reference_manifest": INFERENCE + "/reference_manifest.json",
              "reference_manifest_sha256": "d515497c50bf4f51d9fbd399ef4a00c36ad7bb3da5f1467e574393ff0df15238",
              "cohort": INFERENCE + "/heldout175_manifest.json",
              "cohort_sha256": "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4",
              "exp223_result": REMOTE + "/runs/exp223_official_score175_v2_20260922/output/result.json",
              "exp223_result_sha256": "48e85cda0411325c7b420bc5faa9890e78dda33ac4a9beb7a0112b80848be9c0",
              "exp223_config": CODE + "/exp223_config.json",
              "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
              "data_dir": REMOTE + "/data/exp213_source_view_20260912",
              "output": REMOTE + "/runs/exp228_official_score175_20260926/output"}
    files["score_config.json"] = json.dumps(config, indent=2) + "\n"
    source = '''import ast,hashlib,json,pathlib
p=pathlib.Path(CODE);assert not p.exists();p.mkdir(parents=True)
for name,body in FILES.items():
 q=p/name;q.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
manifest={name:sha(p/name) for name in sorted(FILES)}
(p/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'code':str(p),'files':len(manifest),'manifest_sha256':sha(p/'code_manifest.json'),'score_config_sha256':sha(p/'score_config.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    remote = ssh("nsu-quadro", "python3 -", source)
    receipt = {"status": "PREPARED_EXP228_DIAGNOSTIC_SCORER", "remote": remote,
               "config": config, "no_labels_opened": True}
    (ROOT / "reports/exp228_official_scorer_prepare_20260926.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": remote["manifest_sha256"]}))


if __name__ == "__main__":
    main()
