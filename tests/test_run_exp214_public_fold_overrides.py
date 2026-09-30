import pytest

from scripts.run_exp214_public_fold import parse_override_env


def test_parse_override_env_accepts_biohub_pairs():
    assert parse_override_env(
        [
            "BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE=1",
            "BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_ABS=120",
        ]
    ) == {
        "BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE": "1",
        "BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_ABS": "120",
    }


def test_parse_override_env_rejects_non_biohub_key():
    with pytest.raises(ValueError, match="invalid override key"):
        parse_override_env(["PATH=/tmp"])


def test_parse_override_env_rejects_conflicting_duplicate():
    with pytest.raises(ValueError, match="conflicting override"):
        parse_override_env(["BIOHUB_X=1", "BIOHUB_X=2"])
