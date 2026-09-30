"""Guarded one-shot stage for the sealed EXP209 reconstructed scorer bundle.

Preparation/tests do not invoke this script's execute flag. A created intent
blocks another attempt after any ambiguous SSH result until manual review.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
NAME = "exp209_reconstructed_current_scorer_v1_20260927"
LOCAL_BUNDLE = "work/exp209_reconstructed_scorer_v1_local_20260927/bundle"
MANIFEST_SHA = "2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb"
CONFIG_SHA = "d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335"
SCORER_SHA = "72e24bc53128c1e35ffe7dc806c74ccf0ad36575b52c5d7753ee60e2b3771b79"
CODE_DIR = f"{REMOTE}/code/{NAME}"
RUN_ROOT = f"{REMOTE}/runs/{NAME}"
STAGE_INTENT = f"{REMOTE}/code/.{NAME}.stage_intent.json"
STAGE_COMPLETE = f"{REMOTE}/code/.{NAME}.stage_complete.json"
LOCAL_INTENT = "reports/exp209_reconstructed_scorer_v1_stage_intent_20260927.json"
LOCAL_RECEIPT = "reports/exp209_reconstructed_scorer_v1_stage_20260927.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def valid_name(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name or name.startswith("/"):
        return False
    parts = PurePosixPath(name).parts
    return (len(parts) > 0 and all(part not in ("", ".", "..") for part in parts)
            and PurePosixPath(name).as_posix() == name)


def pack_checked_bundle(bundle: Path) -> tuple[bytes, dict[str, str]]:
    if not __debug__:
        raise RuntimeError("optimized Python disables EXP209 stage guards")
    bundle = bundle.resolve(strict=True)
    manifest_path = bundle / "bundle_manifest.json"
    require(sha(manifest_path) == MANIFEST_SHA, "reviewed scorer manifest SHA mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("experiment") == "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1" and
            manifest.get("status") == "PREPARED_LOCAL_ONLY_NO_LABELS",
            "scorer manifest identity/status mismatch")
    rows = manifest.get("files")
    require(isinstance(rows, list) and len(rows) == 14, "scorer manifest needs 14 payload files")
    names = [row.get("name") for row in rows]
    require(all(valid_name(name) for name in names) and len(set(names)) == 14,
            "unsafe or duplicate scorer payload path")
    require("config.json" in names and "score_exp209_reconstructed_current_v1.py" in names,
            "scorer config/runner absent from manifest")
    require(all(not path.is_symlink() for path in bundle.rglob("*")),
            "scorer bundle contains a symlink")
    expected = set(names) | {"bundle_manifest.json"}
    actual = {path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file()}
    require(actual == expected, "scorer bundle has missing or extra payload")
    hashes = {"bundle_manifest.json": MANIFEST_SHA}
    for row in rows:
        path = bundle / row["name"]
        raw = path.read_bytes()
        require(len(raw) == row["bytes"] and sha_bytes(raw) == row["sha256"],
                f"scorer payload changed: {row['name']}")
        hashes[row["name"]] = row["sha256"]
    require(hashes["config.json"] == CONFIG_SHA and
            hashes["score_exp209_reconstructed_current_v1.py"] == SCORER_SHA,
            "reviewed scorer config/runner SHA mismatch")
    config = json.loads((bundle / "config.json").read_text(encoding="utf-8"))
    require(config["scorer_code_dir"] == CODE_DIR and config["output"] == RUN_ROOT and
            config["reconstruction_gate_sha256"] ==
            "8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1",
            "scorer config code/run/gate pin mismatch")
    with io.BytesIO() as memory:
        with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(expected):
                archive.writestr(name, (bundle / name).read_bytes())
        return memory.getvalue(), hashes


def write_once_durable(path: Path, value: dict) -> None:
    require(path.parent.is_dir() and not path.exists(), f"existing or missing receipt parent: {path}")
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if os.name != "nt":
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def remote_stage_program(payload: bytes, local_intent_sha: str) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f'''import base64,hashlib,io,json,os,pathlib,zipfile
if not __debug__: raise RuntimeError('optimized Python disables stage guards')
code=pathlib.Path({CODE_DIR!r});run=pathlib.Path({RUN_ROOT!r})
intent=pathlib.Path({STAGE_INTENT!r});done=pathlib.Path({STAGE_COMPLETE!r})
assert code.parent==pathlib.Path({(REMOTE+'/code')!r}) and code.name=={NAME!r}
assert run.parent==pathlib.Path({(REMOTE+'/runs')!r}) and run.name=={NAME!r}
assert code.parent.is_dir() and run.parent.is_dir()
assert not code.exists() and not run.exists() and not intent.exists() and not done.exists(), 'stage namespace or intent already exists'
payload=base64.b64decode({encoded!r},validate=True)
assert hashlib.sha256(payload).hexdigest()=={sha_bytes(payload)!r}, 'stage ZIP changed'
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    names=archive.namelist()
    def valid(name):
        pure=pathlib.PurePosixPath(name)
        return (isinstance(name,str) and name and '\\\\' not in name and not name.startswith('/')
                and all(part not in ('','.','..') for part in pure.parts) and pure.as_posix()==name)
    assert len(names)==len(set(names)) and all(valid(name) for name in names), 'unsafe stage ZIP paths'
    manifest_raw=archive.read('bundle_manifest.json')
    assert hashlib.sha256(manifest_raw).hexdigest()=={MANIFEST_SHA!r}, 'remote manifest SHA mismatch'
    manifest=json.loads(manifest_raw)
    assert manifest['experiment']=='EXP209_RECONSTRUCTED_CURRENT_SCORER_V1' and len(manifest['files'])==14
    expected={{row['name'] for row in manifest['files']}} | {{'bundle_manifest.json'}}
    assert set(names)==expected, 'remote ZIP payload set mismatch'
    for row in manifest['files']:
        raw=archive.read(row['name'])
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'], row['name']
    assert hashlib.sha256(archive.read('config.json')).hexdigest()=={CONFIG_SHA!r}
    assert hashlib.sha256(archive.read('score_exp209_reconstructed_current_v1.py')).hexdigest()=={SCORER_SHA!r}
    def once(path,value):
        raw=(json.dumps(value,sort_keys=True,indent=2)+'\\n').encode()
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
        parent=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(parent)
        finally: os.close(parent)
    once(intent,{{'status':'STAGE_INTENT_EXP209_SCORER_V1','bundle_manifest_sha256':{MANIFEST_SHA!r},
                 'config_sha256':{CONFIG_SHA!r},'zip_sha256':{sha_bytes(payload)!r},
                 'local_stage_intent_sha256':{local_intent_sha!r},'labels_read':False,'gpu_used':False}})
    remote_intent_sha=hashlib.sha256(intent.read_bytes()).hexdigest()
    code.mkdir(parents=False,exist_ok=False)
    for name in sorted(names):
        target=code/name
        target.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as stream:
            stream.write(archive.read(name));stream.flush();os.fsync(stream.fileno())
    parent=os.open(code,os.O_RDONLY)
    try: os.fsync(parent)
    finally: os.close(parent)
    actual={{path.relative_to(code).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
            for path in code.rglob('*') if path.is_file()}}
    assert set(actual)==expected and actual['bundle_manifest.json']=={MANIFEST_SHA!r}
    assert all(actual[row['name']]==row['sha256'] for row in manifest['files'])
    complete={{'status':'STAGED_EXP209_SCORER_V1_NO_RUN','code_dir':str(code),
              'run_root':str(run),'bundle_manifest_sha256':{MANIFEST_SHA!r},
              'config_sha256':{CONFIG_SHA!r},'zip_sha256':{sha_bytes(payload)!r},
              'remote_stage_intent_sha256':remote_intent_sha,
              'file_hashes':actual,'file_count':len(actual),'labels_read':False,
              'metric_executed':False,'gpu_used':False}}
    once(done,complete)
    print(json.dumps(complete,sort_keys=True))
'''


def remote_readback_program(local_intent_sha: str) -> str:
    return f'''import hashlib,json,pathlib
code=pathlib.Path({CODE_DIR!r});run=pathlib.Path({RUN_ROOT!r})
done=pathlib.Path({STAGE_COMPLETE!r});intent=pathlib.Path({STAGE_INTENT!r})
assert code.is_dir() and not run.exists() and done.is_file() and intent.is_file()
assert all(not path.is_symlink() for path in code.rglob('*')), 'remote scorer payload symlink'
manifest_raw=(code/'bundle_manifest.json').read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest()=={MANIFEST_SHA!r}
manifest=json.loads(manifest_raw)
expected={{row['name'] for row in manifest['files']}} | {{'bundle_manifest.json'}}
actual={{path.relative_to(code).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
        for path in code.rglob('*') if path.is_file()}}
assert set(actual)==expected and all(actual[row['name']]==row['sha256'] for row in manifest['files'])
assert actual['config.json']=={CONFIG_SHA!r} and actual['score_exp209_reconstructed_current_v1.py']=={SCORER_SHA!r}
complete=json.loads(done.read_text())
assert complete['status']=='STAGED_EXP209_SCORER_V1_NO_RUN' and complete['file_hashes']==actual
remote_intent=json.loads(intent.read_text())
assert remote_intent['status']=='STAGE_INTENT_EXP209_SCORER_V1'
assert remote_intent['local_stage_intent_sha256']=={local_intent_sha!r}
assert complete['remote_stage_intent_sha256']==hashlib.sha256(intent.read_bytes()).hexdigest()
print(json.dumps({{'status':'PASS_EXP209_SCORER_REMOTE_SHA_READBACK','code_dir':str(code),
                  'run_root':str(run),'file_hashes':actual,'file_count':len(actual),
                  'bundle_manifest_sha256':{MANIFEST_SHA!r},'config_sha256':{CONFIG_SHA!r},
                  'remote_stage_intent_sha256':complete['remote_stage_intent_sha256'],
                  'remote_stage_complete_sha256':hashlib.sha256(done.read_bytes()).hexdigest(),
                  'run_absent':True,'labels_read':False,'metric_executed':False}},sort_keys=True))
'''


def ssh_python(host: str, program: str, timeout: int = 180) -> dict:
    result = subprocess.run(["ssh", host, "python3", "-"], input=program, text=True,
                            capture_output=True, timeout=timeout, check=True)
    lines = result.stdout.strip().splitlines()
    require(len(lines) == 1, "remote stage returned ambiguous stdout")
    return json.loads(lines[0])


def stage(root: Path, host: str, expected_manifest_sha: str,
          expected_config_sha: str) -> dict:
    root = root.resolve()
    require(expected_manifest_sha == MANIFEST_SHA and expected_config_sha == CONFIG_SHA,
            "reviewed EXP209 scorer manifest/config SHA arguments required")
    bundle = root / LOCAL_BUNDLE
    payload, expected_hashes = pack_checked_bundle(bundle)
    intent_path = root / LOCAL_INTENT
    receipt_path = root / LOCAL_RECEIPT
    require(not intent_path.exists() and not receipt_path.exists(),
            "EXP209 scorer stage already attempted; reconcile before any new version")
    local_intent = {"status": "STAGE_INTENT_EXP209_SCORER_V1_LOCAL",
                    "bundle_manifest_sha256": MANIFEST_SHA,
                    "config_sha256": CONFIG_SHA,
                    "zip_sha256": sha_bytes(payload),
                    "remote_code_dir": CODE_DIR, "remote_run_root": RUN_ROOT,
                    "stage_source_sha256": sha(Path(__file__)),
                    "remote_stage": "UNATTEMPTED", "labels_read": False}
    write_once_durable(intent_path, local_intent)
    # No catch/retry: a timeout or ambiguous SSH result leaves the durable intent.
    staged = ssh_python(host, remote_stage_program(payload, sha(intent_path)))
    require(staged.get("status") == "STAGED_EXP209_SCORER_V1_NO_RUN" and
            staged.get("code_dir") == CODE_DIR and staged.get("run_root") == RUN_ROOT and
            staged.get("file_hashes") == expected_hashes and
            staged.get("file_count") == 15 and staged.get("labels_read") is False and
            staged.get("metric_executed") is False,
            "remote stage response differs from sealed local bundle")
    readback = ssh_python(host, remote_readback_program(sha(intent_path)))
    require(readback.get("status") == "PASS_EXP209_SCORER_REMOTE_SHA_READBACK" and
            readback.get("file_hashes") == expected_hashes and
            readback.get("bundle_manifest_sha256") == MANIFEST_SHA and
            readback.get("config_sha256") == CONFIG_SHA and
            readback.get("remote_stage_intent_sha256") ==
            staged.get("remote_stage_intent_sha256") and
            readback.get("run_absent") is True and
            readback.get("labels_read") is False and
            readback.get("metric_executed") is False,
            "post-stage remote SHA readback mismatch")
    receipt = {"status": "PASS_EXP209_SCORER_V1_STAGED_NO_RUN",
               "code_dir": CODE_DIR, "run_root": RUN_ROOT,
               "bundle_manifest_sha256": MANIFEST_SHA,
               "config_sha256": CONFIG_SHA,
               "zip_sha256": sha_bytes(payload),
               "file_hashes": expected_hashes,
               "local_stage_intent_sha256": sha(intent_path),
               "remote_stage_intent_sha256": readback["remote_stage_intent_sha256"],
               "remote_stage_complete_sha256": readback["remote_stage_complete_sha256"],
               "stage_source_sha256": sha(Path(__file__)),
               "labels_read": False, "metric_executed": False,
               "gpu_used": False, "remote_run_created": False}
    write_once_durable(receipt_path, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="nsu-quadro")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--execute-reviewed-stage", action="store_true", required=True)
    args = parser.parse_args()
    result = stage(args.root, args.host, args.expected_manifest_sha256,
                   args.expected_config_sha256)
    print(json.dumps({"status": result["status"], "file_count": len(result["file_hashes"]),
                      "remote_stage_complete_sha256": result["remote_stage_complete_sha256"]}))


if __name__ == "__main__":
    main()
