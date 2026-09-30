from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_exp163_launcher_pins_exact_checkpoint_hashes():
    source = (ROOT / "scripts/run_exp163_visual_pair_ensemble.sh").read_text()
    expected = {
        "--backbone-sha256": "3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e",
        "--scratch-sha256": "167f50a77587571bc9d01f1da645deb2a3de1e56bb8608f39d3f0ebd587427fb",
        "--feature-sha256": "3cdc17023606b8193cd01f1da645deb2a3de1e56bb8608f39d3f0ebd587427fb",
    }
    for flag, digest in expected.items():
        match = re.search(rf"{re.escape(flag)}\s+(\S+)", source)
        assert match is not None
        assert match.group(1) == digest
        assert re.fullmatch(r"[0-9a-f]{64}", match.group(1))


def test_exp163_launcher_is_external_only():
    source = (ROOT / "scripts/run_exp163_visual_pair_ensemble.sh").read_text().lower()
    assert "zebrahub_training_set" in source
    assert "competition" not in source
    assert "target" not in source
