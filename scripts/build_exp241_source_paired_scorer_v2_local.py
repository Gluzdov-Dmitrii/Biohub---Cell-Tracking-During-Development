"""One-shot local copy of sealed EXP241 v1 with only the gate typo and v2 identity fixed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "work/exp241_source_paired_scorer_v1_20260927"
V2 = ROOT / "work/exp241_source_paired_scorer_v2_20260927"
V1_MANIFEST_SHA = "bd585c361c68b8b9e67bd1ebe0ba132a11c682dd5dec2116de6f78b36e714975"
V1_GATE_TYPO = "735496f5cf6d2a24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
ACTUAL_GATE = "735496f5cf6dca2e24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
OLD_RUN = "exp241_source_paired_scorer_v1_20260927"
NEW_RUN = "exp241_source_paired_scorer_v2_20260927"
OLD_STATUS = "SEALED_EXP241_SOURCE_PAIRED_SCORER_V1"
NEW_STATUS = "SEALED_EXP241_SOURCE_PAIRED_SCORER_V2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_exact(data: bytes, old: str, new: str, count: int) -> bytes:
    source, dest = old.encode(), new.encode()
    assert data.count(source) == count, old
    return data.replace(source, dest)


def main() -> None:
    assert not V2.exists(), "Never overwrite a sealed v2 package"
    assert sha((V1 / "manifest.json").read_bytes()) == V1_MANIFEST_SHA
    manifest = json.loads((V1 / "manifest.json").read_text())
    assert manifest["status"] == OLD_STATUS and len(manifest["files"]) == 12
    found = {p.relative_to(V1).as_posix() for p in V1.rglob("*") if p.is_file()}
    assert found == set(manifest["files"]) | {"manifest.json"}
    for name, digest in manifest["files"].items():
        assert sha((V1 / name).read_bytes()) == digest, name
    V2.mkdir(parents=True, exist_ok=False)
    new_files = {}
    for name in manifest["files"]:
        data = (V1 / name).read_bytes()
        if name == "score_exp241_source_paired.py":
            data = replace_exact(data, V1_GATE_TYPO, ACTUAL_GATE, 1)
            data = replace_exact(data, OLD_RUN + "/output", NEW_RUN + "/output", 1)
            data = replace_exact(data, OLD_STATUS, NEW_STATUS, 2)
        elif name == "config.json":
            data = replace_exact(data, OLD_RUN + "/output", NEW_RUN + "/output", 1)
            data = replace_exact(data, OLD_STATUS, NEW_STATUS, 1)
        dest = V2 / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        new_files[name] = sha(data)
    new_manifest = {"status": NEW_STATUS, "files": new_files}
    (V2 / "manifest.json").write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": NEW_STATUS,
                      "manifest_sha256": sha((V2 / "manifest.json").read_bytes()),
                      "runner_sha256": new_files["score_exp241_source_paired.py"],
                      "config_sha256": new_files["config.json"],
                      "unchanged_files": sum(manifest["files"][n] == d for n, d in new_files.items()),
                      "source_labels_read": False, "remote_mutation": False}))


if __name__ == "__main__":
    main()
