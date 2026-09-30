import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mark_exp192_runs_data_ready as marker
import verify_exp192_data_ready_receipts as verifier
from validate_exp192_chunk_structure import sha256


def make_fixture(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    for name in marker.CODE_FILES:
        (code / name).write_text(name, encoding="utf-8")
    audit = tmp_path / "audit.json"
    payload = dict(marker.EXPECTED_AUDIT)
    payload.update({"content_sha256_by_movie": {f"m{i}": "a" * 64 for i in range(175)}, "manifest_sha256": "b" * 64})
    audit.write_text(json.dumps(payload), encoding="utf-8")
    runs = tmp_path / "runs"
    chunks = []
    for direction, sizes in (("forward", [24, 24, 24, 24, 20]), ("reverse", [24, 24, 11])):
        for number, size in enumerate(sizes):
            run = runs / f"exp192_confirm_{direction}_{number:02d}_20260911"
            run.mkdir(parents=True)
            movies = run / "movies.json"
            movies.write_text(json.dumps({"movies": list(range(size))}), encoding="utf-8")
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": sha256(movies)})
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps(marker.mark(audit, index, runs, code)), encoding="utf-8")
    return summary, audit, index, runs, code


def test_verifies_exact_eight_chunk_transaction(tmp_path):
    args = make_fixture(tmp_path)
    result = verifier.verify(*args)
    assert result["status"] == "PASS_EXP192_DATA_READY_FINALIZATION"
    assert result["chunks"] == 8
    assert len(result["verified"]) == 8


def test_rejects_tampered_receipt(tmp_path):
    summary, audit, index, runs, code = make_fixture(tmp_path)
    receipt = runs / "exp192_confirm_forward_00_20260911" / "data_ready.json"
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["movies"] = 23
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    try:
        verifier.verify(summary, audit, index, runs, code)
    except ValueError as exc:
        assert "summary SHA mismatch" in str(exc)
    else:
        raise AssertionError("tampered receipt was accepted")
