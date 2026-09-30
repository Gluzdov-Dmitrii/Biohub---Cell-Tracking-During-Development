import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_relocated_sha256sums", ROOT / "scripts" / "verify_relocated_sha256sums.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_verifies_exact_relocation(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    new.mkdir()
    (new / "a.json").write_bytes(b"alpha")
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{digest(b'alpha')}  {old / 'a.json'}\n", encoding="utf-8")
    rows = MODULE.verify(manifest, old, new)
    assert rows == [(digest(b"alpha"), (new / "a.json").resolve())]


def test_rejects_hash_mismatch(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    new.mkdir()
    (new / "a.json").write_bytes(b"changed")
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{digest(b'alpha')}  {old / 'a.json'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA mismatch"):
        MODULE.verify(manifest, old, new)


def test_rejects_path_outside_old_root(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    new.mkdir()
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{'a' * 64}  {tmp_path / 'elsewhere.json'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside exact old root"):
        MODULE.verify(manifest, old, new)
