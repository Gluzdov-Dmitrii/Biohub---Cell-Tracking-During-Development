from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage_launcher_is_single_use_and_pins_archive_and_runner() -> None:
    source = (ROOT / "scripts" / "launch_exp192_stage_remote.sh").read_text(encoding="utf-8")
    assert "87393127165" in source
    assert "538ed8a4d7b6669fa948865f947ed43c23aba7ee006fea8826d6ddd1277dfd19" in source
    assert "1d39c8a3f8e34d56c25ec935759fbfc0f7b147b7a9fb4886309eb27f31615213" in source
    assert ".stage-launch-lock" in source
    assert "stage_launch_receipt.txt" in source
    assert "pgrep -af" in source
    assert '[[ $(find "$stage" -mindepth 1 -maxdepth 1 | wc -l) -eq 1 ]]' in source
    assert 'nohup bash "$runner"' in source
    assert "start_tick" in source
