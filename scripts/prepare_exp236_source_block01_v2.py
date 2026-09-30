"""Freeze and stage EXP236 source6bba block01 v2 after the duplicate-frame fix."""
import base64
import hashlib
import json
from pathlib import Path
import shlex

from exp236_duplicate_frame_safeguard import patch_horaz_datasets
from monitor_exp213_job import QUEUE, ssh
from run_exp236_source_block01_v2 import SOURCE_BUNDLE, SOURCE_BUNDLE_SHA, validate


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
DATA = REMOTE + "/data/exp213_source_view_20260912"
CODE = REMOTE + "/code/exp236_horaz_source6bba_block01_v2_20260927"
RUN = REMOTE + "/runs/exp236_horaz_source6bba_block01_v2_20260927"
WORK = ROOT / "work/exp236_source6bba_v2_20260927"
PREPARE_RECEIPT = ROOT / "reports/exp236_source_block01_v2_prepare_20260927.json"
CONFIG_RECEIPT = ROOT / "reports/exp236_source_block01_v2_config_20260927.json"
SOURCE_MANIFEST_SHA256 = "a5c3176ec25d4d75321e6c1fe17b62be2d9e25472ae7fcb677e48fe71478bd87"
PLAN_SHA256 = "e525d6f44f45468520fa085836ce4c166f594dbc5d64e79c7e15a10083e5c536"
CODE_MANIFEST_SHA256 = "b594f5ca6e2c644b151d780546cab140208f08558d1b93b24cef7a576a6e5f4a"
RAW_AUDIT_RECEIPT = ROOT / "reports/exp236_duplicate_source_audit_20260927.json"
EFFECTIVE_AUDIT_RECEIPT = ROOT / "reports/exp236_effective_source_audit_20260927.json"
RAW_AUDIT_SHA256 = "5809c021723877a804331a7cbc0629565ca98d981dbba4a58385f33f4455db8f"
EFFECTIVE_AUDIT_SHA256 = "0f2e322a2581fba4f0cd2bca43bea1adf2616893ecce32043e6f3f90fe5298cb"
V1_CODE = REMOTE + "/code/exp236_horaz_source6bba_block01_20260927"
V1_RUN = REMOTE + "/runs/exp236_horaz_source6bba_block01_20260927"
V1_PLAN_SHA256 = "d75ffd601e0e8409976fd74a854d704f598f758bd250c4d552d985dda475a1c5"
V1_CODE_MANIFEST_SHA256 = "5419ab1049c7cdf11fc4c6d79f0a0e180b8285ab07fc3331db0d64dbfcd998fb"
V1_LEASE_ID = "exp236-horaz-source6bba-block01-20260927"
V1_ERROR = "AssertionError('Consecutive duplicate frames in 6bba_7f87b3d8: t=82 and t=83')"


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def _audit_pairs(audit, pair_key):
    """Normalize an all-source receipt's duplicate pairs by dataset."""
    assert audit["plan_sha256"] == V1_PLAN_SHA256
    assert audit["movies_scanned"] == 126 and audit["target_data_opened"] is False
    per_movie = audit["per_movie"]
    assert audit["movies_with_duplicates"] == len(per_movie)
    assert audit["duplicate_pairs"] == sum(len(row[pair_key]) for row in per_movie)
    normalized = {}
    derived_inconsistent = set()
    sampled_count = 0
    for row in per_movie:
        dataset_id = row["dataset"]
        assert dataset_id.startswith("6bba_") and dataset_id not in normalized
        assert row["split"] in ("train", "inner_validation")
        starts = []
        for pair in row[pair_key]:
            start = pair["t0"]
            assert isinstance(start, int) and 0 <= start < 99
            assert pair["t1"] == start + 1
            assert pair["sampled"] in (True, False)
            assert pair["labels_concordant"] in (True, False)
            if pair["sampled"]:
                sampled_count += 1
                if not pair["labels_concordant"]:
                    derived_inconsistent.add((dataset_id, start))
            starts.append(start)
        assert starts == sorted(set(starts))
        normalized[dataset_id] = starts
    reported_inconsistent = {(row["dataset"], row["t0"])
                             for row in audit["inconsistent_sampled_pairs"]}
    assert reported_inconsistent == derived_inconsistent
    if "sampled_duplicate_pairs" in audit:
        assert audit["sampled_duplicate_pairs"] == sampled_count
    return normalized, derived_inconsistent


def verify_source_audits(raw_path=None, effective_path=None):
    """Bind both completed 126-movie source audits before stage or launch."""
    raw_body = Path(raw_path or RAW_AUDIT_RECEIPT).read_bytes()
    effective_body = Path(effective_path or EFFECTIVE_AUDIT_RECEIPT).read_bytes()
    assert sha_bytes(raw_body) == RAW_AUDIT_SHA256
    assert sha_bytes(effective_body) == EFFECTIVE_AUDIT_SHA256
    raw = json.loads(raw_body)
    effective = json.loads(effective_body)
    assert raw["status"] == "FAIL_EXP236_SOURCE_DUPLICATE_AUDIT"
    assert effective["status"] == "AUDITED_EXP236_EFFECTIVE_SOURCE_DUPLICATES"
    assert effective["resolved_config_sha256"] == "6854b15c8facdb7216e8546fe8f461d2c673770b032fdab6a4e5bbc3b6d508fe"
    assert effective["downsample"] == [1, 4, 4] and effective["window_size"] == 2
    assert raw["duplicate_pairs"] == effective["duplicate_pairs"] == 927
    assert raw["movies_with_duplicates"] == effective["movies_with_duplicates"] == 112
    assert effective["sampled_duplicate_pairs"] == 910
    raw_pairs, raw_inconsistent = _audit_pairs(raw, "duplicates")
    effective_pairs, effective_inconsistent = _audit_pairs(effective, "pairs")
    assert raw_pairs == effective_pairs
    assert raw_inconsistent == effective_inconsistent
    assert len(effective_inconsistent) == 43
    assert 39 in effective_pairs["6bba_7f87b3d8"]
    excluded_by_split = {split: sum(len(row["pairs"]) for row in effective["per_movie"]
                                    if row["split"] == split)
                         for split in ("train", "inner_validation")}
    removed_sampled_by_split = {
        split: sum(pair["sampled"] for row in effective["per_movie"]
                   if row["split"] == split for pair in row["pairs"])
        for split in ("train", "inner_validation")
    }
    assert excluded_by_split == {"train": 824, "inner_validation": 103}
    assert removed_sampled_by_split == {"train": 809, "inner_validation": 101}
    return {"raw_sha256": sha_bytes(raw_body),
            "effective_sha256": sha_bytes(effective_body),
            "movies_scanned": 126,
            "raw_duplicate_pairs": raw["duplicate_pairs"],
            "effective_duplicate_pairs": effective["duplicate_pairs"],
            "inconsistent_sampled_pairs": len(effective_inconsistent),
            "excluded_pairs_by_split": excluded_by_split,
            "removed_sampled_windows_by_split": removed_sampled_by_split,
            "duplicate_starts": effective_pairs,
            "target_data_opened": False}


def validate_parent_failure(parent, queue_state):
    """Pin the failed v1 attempt and its live released lease."""
    assert parent["code_manifest_sha256"] == V1_CODE_MANIFEST_SHA256
    assert parent["plan_sha256"] == V1_PLAN_SHA256
    result = parent["result"]
    assert result["status"] == "FAILED_EXP236_SOURCE_BLOCK01"
    assert result["error"] == V1_ERROR
    assert result["plan_sha256"] == V1_PLAN_SHA256
    assert result["target_data_opened"] is False
    assert parent["exit"] == {"returncode": 1, "hard_timeout": False}
    assert parent["supervision"] == {"status": "RELEASED_AFTER_VERIFIED_EXIT",
                                     "exit_matches": True}
    assert parent["control"] == {"action": "release", "queue_state": "RELEASED",
                                 "queue_id": V1_LEASE_ID, "queue_run_path": V1_RUN}
    rows = [row for row in queue_state["requests"] if row["id"] == V1_LEASE_ID]
    assert len(rows) == 1
    assert rows[0]["state"] == "RELEASED" and rows[0]["run_path"] == V1_RUN
    return {"status": "PASS_EXP236_V1_FAILED_AND_RELEASED",
            "error": V1_ERROR, "returncode": 1, "hard_timeout": False,
            "lease_id": V1_LEASE_ID, "queue_state": "RELEASED",
            "plan_sha256": V1_PLAN_SHA256,
            "code_manifest_sha256": V1_CODE_MANIFEST_SHA256,
            "target_data_opened": False}


def verify_parent_failure():
    source = '''import hashlib,json,pathlib
code=pathlib.Path(V1_CODE);run=pathlib.Path(V1_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda name:json.loads((run/name).read_text())
result=read('output/result.json');exit_record=read('exit.json')
supervision=read('supervision/complete.json');control=read('supervision/control.json')
queue=control['queue']
print(json.dumps({'code_manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),
 'result':{key:result.get(key) for key in ('status','error','plan_sha256','target_data_opened')},
 'exit':{key:exit_record.get(key) for key in ('returncode','hard_timeout')},
 'supervision':{'status':supervision.get('status'),'exit_matches':supervision.get('exit')==exit_record},
 'control':{'action':control.get('action'),'queue_state':queue.get('state'),
            'queue_id':queue.get('id'),'queue_run_path':queue.get('run_path')}}))
'''.replace("V1_CODE", repr(V1_CODE)).replace("V1_RUN", repr(V1_RUN))
    parent = ssh("nsu-a100", "python3 -", source)
    queue_state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    return validate_parent_failure(parent, queue_state)


def build_payload(source, audits):
    """Build the exact stage bytes from the pinned source-only cohort."""
    assert source["bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert len(source["train"]) == 115 and len(source["inner_validation"]) == 11
    assert len(set(source["train"] + source["inner_validation"])) == 126
    assert all(name.startswith("6bba_") for name in source["train"] + source["inner_validation"])
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
    ids = source["train"] + source["inner_validation"]
    assert set(audits["duplicate_starts"]) <= set(ids)
    pair_map = {"source_embryo": "6bba", "loader_view": "float32_zarr_downsample_1_4_4",
                "window_size": 2, "source_dataset_ids": ids,
                "raw_audit_sha256": audits["raw_sha256"],
                "effective_audit_sha256": audits["effective_sha256"],
                "excluded_pairs_by_split": audits["excluded_pairs_by_split"],
                "removed_sampled_windows_by_split": audits["removed_sampled_windows_by_split"],
                "duplicate_starts": audits["duplicate_starts"]}
    pair_map_body = (json.dumps(pair_map, indent=2, sort_keys=True) + "\n").encode()
    plan = {"experiment": "EXP236", "purpose": "source_only_reciprocal_horaz_block01",
            "source_embryo": "6bba", "target_embryo": "44b6", "fold": 0,
            "block_end_epoch": 3, "planned_epochs": 50, "resume": False,
            "source_duplicate_policy": "exclude_all_effective_duplicate_windows_v2",
            "source_duplicate_map_sha256": sha_bytes(pair_map_body),
            "excluded_pairs_by_split": audits["excluded_pairs_by_split"],
            "removed_sampled_windows_by_split": audits["removed_sampled_windows_by_split"],
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
    datasets_name = "horaz/src/src/datasets.py"
    files[datasets_name] = patch_horaz_datasets(files[datasets_name])
    files["horaz/src/src/exp236_duplicate_frame_safeguard.py"] = (
        ROOT / "scripts/exp236_duplicate_frame_safeguard.py").read_bytes()
    files["horaz/src/src/exp236_source_duplicate_pairs.json"] = pair_map_body
    for name in ("run_exp236_source_block01_v2.py", "run_exp226_source_pilot.py",
                 "exp226_protocol.py", "exp223_supervisor.py", "monitor_exp213_job.py"):
        files[name] = (ROOT / "scripts" / name).read_bytes()
    wrapper = (ROOT / "scripts/exp214_inference_job.py").read_text()
    old = "assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
    assert wrapper.count(old) == 1
    files["exp227_job.py"] = wrapper.replace(
        old, "assert config['script'] == 'run_exp236_source_block01_v2.py'").encode()
    files["source6bba_manifest.json"] = manifest_body
    files["plan.json"] = plan_body
    hashes = {name: sha_bytes(body) for name, body in sorted(files.items())}
    files["code_manifest.json"] = json.dumps(hashes, indent=2).encode()
    return manifest_body, plan_body, files


def main():
    assert not WORK.exists()
    assert not PREPARE_RECEIPT.exists() and not CONFIG_RECEIPT.exists()
    audits = verify_source_audits()
    parent_failure = verify_parent_failure()
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
print(json.dumps({'status':'PASS_EXP236_SOURCE6BBA_V2_PREFLIGHT',
 'bundle_sha256':sha(bundle),'training_plan_sha256':obj['training_plan_sha256'],
 'train':train,'inner_validation':inner}))
'''.replace("BUNDLE_SHA", repr(SOURCE_BUNDLE_SHA)).replace("BUNDLE", repr(SOURCE_BUNDLE)).replace(
        "DATA", repr(DATA)).replace("CODE", repr(CODE)).replace("RUN", repr(RUN))
    source = ssh("nsu-a100", "python3 -", preflight)
    assert source["status"] == "PASS_EXP236_SOURCE6BBA_V2_PREFLIGHT"
    manifest_body, plan_body, files = build_payload(source, audits)
    assert sha_bytes(manifest_body) == SOURCE_MANIFEST_SHA256
    assert sha_bytes(plan_body) == PLAN_SHA256
    assert sha_bytes(files["code_manifest.json"]) == CODE_MANIFEST_SHA256
    stage = '''import ast,base64,hashlib,json,pathlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir()
for name,value in FILES.items():
 path=code/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(value))
 if name.endswith('.py'):ast.parse(path.read_text(),filename=str(path))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
print(json.dumps({'status':'STAGED_EXP236_SOURCE6BBA_BLOCK01_V2',
 'code':str(code),'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'source_manifest_sha256':sha(code/'source6bba_manifest.json')}))
'''.replace("CODE", repr(CODE)).replace(
        "FILES", repr({name: base64.b64encode(body).decode() for name, body in files.items()}))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP236_SOURCE6BBA_BLOCK01_V2"
    assert staged["manifest_sha256"] == sha_bytes(files["code_manifest.json"])
    assert staged["plan_sha256"] == sha_bytes(plan_body)
    assert staged["source_manifest_sha256"] == sha_bytes(manifest_body)

    WORK.mkdir(parents=True)
    (WORK / "source6bba_manifest.json").write_bytes(manifest_body)
    (WORK / "plan.json").write_bytes(plan_body)
    (WORK / "code_manifest.json").write_bytes(files["code_manifest.json"])
    config = {"experiment": "EXP236",
              "lease_id": "exp236-horaz-source6bba-block01-v2-20260927",
              "token": "exp236_horaz_source6bba_block01_v2_20260927",
              "code": CODE, "run": RUN, "max_seconds": 10800,
              "cpu_affinity": "0-7", "script": "run_exp236_source_block01_v2.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    CONFIG_RECEIPT.write_text(json.dumps(config, indent=2) + "\n")
    audit_summary = {key: value for key, value in audits.items() if key != "duplicate_starts"}
    receipt = {"status": "PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS",
               "parent_failure": parent_failure, "source_duplicate_audits": audit_summary,
               "preflight": {key: source[key] for key in ("status", "bundle_sha256", "training_plan_sha256")},
               "stage": staged, "train_movies": 115, "inner_validation_movies": 11,
               "source_duplicate_policy": "exclude_all_effective_duplicate_windows_v2",
               "target_data_opened": False}
    PREPARE_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "plan_sha256": staged["plan_sha256"]}))


if __name__ == "__main__":
    main()
