import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from verify_exp207_manifest_without_temp import verify


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path: Path):
    code = tmp_path / "code"
    gpu = tmp_path / "gpu"
    results = gpu / "results"
    code.mkdir()
    results.mkdir(parents=True)
    source = code / "source.py"
    metric = results / "metric.json"
    source.write_text("print('fixed')\n", encoding="utf-8")
    metric.write_text("{\"score\": 1}\n", encoding="utf-8")
    manifest = results / "SHA256SUMS"
    missing_temp = results / "SHA256SUMS.tmp"
    manifest.write_text(
        f"{digest(source)}  {source.resolve()}\n"
        f"{digest(metric)}  {metric.resolve()}\n"
        f"{'0' * 64}  {missing_temp.resolve()}\n",
        encoding="utf-8",
    )
    return manifest, code, gpu, metric


def test_accepts_only_the_expected_missing_self_temp(tmp_path):
    manifest, code, gpu, _ = fixture(tmp_path)
    result = verify(manifest, code, gpu)
    assert result["status"].startswith("PASS_EXP207")
    assert result["verified_existing_entries"] == 2
    assert result["exact_current_file_coverage"] is True


def test_rejects_hash_mismatch(tmp_path):
    manifest, code, gpu, metric = fixture(tmp_path)
    metric.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA mismatch"):
        verify(manifest, code, gpu)


def test_rejects_unlisted_file(tmp_path):
    manifest, code, gpu, _ = fixture(tmp_path)
    (gpu / "surprise.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="coverage mismatch"):
        verify(manifest, code, gpu)


def test_rejects_second_missing_file(tmp_path):
    manifest, code, gpu, metric = fixture(tmp_path)
    metric.unlink()
    with pytest.raises(ValueError, match="Expected only missing temp entry"):
        verify(manifest, code, gpu)
