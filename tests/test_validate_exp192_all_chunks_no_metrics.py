import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_exp192_all_chunks_no_metrics as module


def test_validates_exact_175_coverage_without_metrics(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    chunks = []
    specs = [("forward", [24, 24, 24, 24, 20], "6bba"), ("reverse", [24, 24, 11], "44b6")]
    offset = {"forward": 0, "reverse": 0}
    for direction, sizes, prefix in specs:
        for number, size in enumerate(sizes):
            label = f"{direction}_{number:02d}"
            run = runs / f"exp192_confirm_{label}_20260911"
            run.mkdir(parents=True)
            movies = [f"{prefix}_{i:04}.zarr" for i in range(offset[direction], offset[direction] + size)]
            offset[direction] += size
            path = run / "movies.json"
            path.write_text(json.dumps({"target_development": movies}), encoding="utf-8")
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": module.sha256(path)})
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")

    def fake_validate(run_dir, direction):
        count = len(json.loads((run_dir / "movies.json").read_text())["target_development"])
        return {"movie_count": count, "scientific_metrics_emitted": False, "validated_files": [{"sha256": "a" * 64}]}

    monkeypatch.setattr(module, "validate_chunk", fake_validate)
    result = module.validate_all(index, runs)
    assert result["status"] == "PASS_EXP192_ALL_CHUNKS_NO_METRICS"
    assert result["movie_counts"]["combined"] == 175
    assert result["scientific_metrics_emitted"] is False
