import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mark_exp192_runs_data_ready as module
from validate_exp192_chunk_structure import sha256


def test_marks_all_runs_only_after_full_audit(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    for name in module.CODE_FILES:
        (code / name).write_text(name)
    audit = tmp_path / "audit.json"
    audit_payload = dict(module.EXPECTED_AUDIT)
    audit_payload.update({"content_sha256_by_movie": {f"m{i}": "a" * 64 for i in range(175)}, "manifest_sha256": "b" * 64})
    audit.write_text(json.dumps(audit_payload))
    runs = tmp_path / "runs"
    chunks = []
    for direction, sizes in (("forward", [24, 24, 24, 24, 20]), ("reverse", [24, 24, 11])):
        for number, size in enumerate(sizes):
            run = runs / f"exp192_confirm_{direction}_{number:02d}_20260911"
            run.mkdir(parents=True)
            movies = run / "movies.json"
            movies.write_text(json.dumps({"target_development": [f"{direction}_{number}_{i}" for i in range(size)]}))
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": sha256(movies)})
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"chunks": chunks}))
    result = module.mark(audit, index, runs, code)
    assert len(result) == 8
    assert all((runs / item["run_id"] / "data_ready.json").is_file() for item in result)
    receipt = json.loads((runs / result[0]["run_id"] / "data_ready.json").read_text())
    assert set(receipt["code_sha256"]) == set(module.CODE_FILES)
