"""One-shot stage of reviewed EXP209 CPU reconstruction v1 bundle.

Preparation and tests never invoke this script with its execute flag.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

from prepare_exp209_reconstruction_v1_local import CODE_NAME, LOCAL_WORK, REMOTE_ROOT


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_checked_bundle(bundle: Path) -> tuple[bytes, str, int]:
    if not __debug__:
        raise RuntimeError("optimized Python disables stage guards")
    manifest_path = bundle / "bundle_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["experiment"] == "EXP209_CURRENT_METRIC_RECONSTRUCTION_V1"
    expected = {entry["name"] for entry in manifest["files"]} | {"bundle_manifest.json"}
    assert {path.name for path in bundle.iterdir() if path.is_file()} == expected
    assert len(expected) == len(manifest["files"]) + 1
    for item in manifest["files"]:
        path = bundle / item["name"]
        assert path.is_file() and len(path.read_bytes()) == item["bytes"]
        assert sha256(path.read_bytes()) == item["sha256"]
    with io.BytesIO() as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(expected):
                archive.write(bundle / name, arcname=name)
        return stream.getvalue(), sha256(manifest_bytes), len(expected)


def remote_stage_program(payload: bytes, manifest_sha: str, remote_target: str) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f'''import base64,hashlib,io,json,os,pathlib,zipfile
if not __debug__: raise RuntimeError('optimized Python disables stage guards')
target=pathlib.Path({remote_target!r})
assert target.parent==pathlib.Path({(REMOTE_ROOT + '/code')!r})
assert not target.exists(), 'immutable reconstruction code namespace already exists'
data=base64.b64decode({encoded!r})
with zipfile.ZipFile(io.BytesIO(data)) as z:
    names=z.namelist()
    assert len(names)==len(set(names)) and all(pathlib.Path(n).name==n and n not in ('','.', '..') for n in names)
    manifest_bytes=z.read('bundle_manifest.json')
    assert hashlib.sha256(manifest_bytes).hexdigest()=={manifest_sha!r}
    manifest=json.loads(manifest_bytes)
    expected={{row['name'] for row in manifest['files']}} | {{'bundle_manifest.json'}}
    assert set(names)==expected
    for row in manifest['files']:
        raw=z.read(row['name'])
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    target.mkdir(parents=False,exist_ok=False)
    for name in names:
        raw=z.read(name)
        with (target/name).open('xb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    assert hashlib.sha256((target/'bundle_manifest.json').read_bytes()).hexdigest()=={manifest_sha!r}
print(json.dumps({{'status':'STAGED_EXP209_RECONSTRUCTION_V1_NO_RUN','code_dir':str(target),'bundle_manifest_sha256':{manifest_sha!r},'file_count':len(names),'labels_read':False,'gpu_used':False}}))
'''


def write_once(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644), "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def stage(root: Path, host: str, expected_manifest_sha: str) -> dict:
    bundle = root / LOCAL_WORK / "bundle"
    payload, manifest_sha, count = pack_checked_bundle(bundle)
    assert len(expected_manifest_sha) == 64 and manifest_sha == expected_manifest_sha, "reviewed bundle SHA mismatch"
    target = REMOTE_ROOT + "/code/" + CODE_NAME
    receipt = root / "reports/exp209_reconstruction_v1_stage_20260927.json"
    assert not receipt.exists(), "one-shot stage receipt already exists"
    script = remote_stage_program(payload, manifest_sha, target)
    result = subprocess.run(["ssh", host, "python3", "-"], input=script, text=True,
                            capture_output=True, timeout=180, check=True)
    response = json.loads(result.stdout.strip())
    assert response == {"status": "STAGED_EXP209_RECONSTRUCTION_V1_NO_RUN",
                        "code_dir": target, "bundle_manifest_sha256": manifest_sha,
                        "file_count": count, "labels_read": False, "gpu_used": False}
    write_once(receipt, {**response, "local_bundle": str(bundle),
                         "stage_script_sha256": sha256(Path(__file__).read_bytes()),
                         "remote_action": "code stage only; no reconstruction launch"})
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="nsu-quadro")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--execute-reviewed-stage", action="store_true", required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.root.resolve(), args.host, args.expected_manifest_sha256), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
