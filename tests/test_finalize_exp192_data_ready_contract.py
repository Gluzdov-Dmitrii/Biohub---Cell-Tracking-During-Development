from pathlib import Path


def test_finalizer_is_single_use_and_stage_gated():
    text = (Path(__file__).resolve().parents[1] / "scripts" / "finalize_exp192_data_ready.sh").read_text(encoding="utf-8")
    assert "PASS_EXP192_REMOTE_STAGE" in text
    assert "sha256sum -c" in text
    assert "pgrep -af" in text
    assert "[[ ! -e \"$run/data_ready.json\" ]]" in text
    assert "mark_exp192_runs_data_ready.py" in text
    assert "verify_exp192_data_ready_receipts.py" in text
    assert "9a8e531210066dcf2d18da3fc0b58272b449110f80c9b2a24df9537916afa42d" in text
    assert "mv \"$temporary\" \"$summary\"" in text
    assert text.index("mark_exp192_runs_data_ready.py") < text.index("PASS_EXP192_DATA_READY")
