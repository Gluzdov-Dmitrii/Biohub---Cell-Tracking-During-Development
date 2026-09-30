import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_exp164_launcher_matches_raw_result_and_all_exact_hashes():
    source = (ROOT / "scripts/run_exp164_visual_pair_ensemble.sh").read_text()
    raw = json.loads((ROOT / "outputs/research/exp130_official24_private_first/exp160_external/external_result.json").read_text())
    expected = {
        "--backbone-sha256": "3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e",
        "--scratch-sha256": "167f50a77587571bc9d01f1da645deb2a3de1e56bb8608f39d3f0ebd587427fb",
        "--feature-sha256": raw["head_checkpoint_sha256"],
    }
    assert expected["--feature-sha256"] == "3cdc17023606b8193cbdfb97f1035a5e8383a17763764b80c2c99ae0f1590d38"
    for flag, digest in expected.items():
        match = re.search(rf"{re.escape(flag)}\s+([0-9a-f]+)", source)
        assert match is not None
        assert match.group(1) == digest
        assert len(digest) == 64


def test_exp164_launcher_is_external_only():
    source = (ROOT / "scripts/run_exp164_visual_pair_ensemble.sh").read_text().lower()
    assert "zebrahub_training_set" in source
    assert "competition" not in source
    assert "target" not in source
