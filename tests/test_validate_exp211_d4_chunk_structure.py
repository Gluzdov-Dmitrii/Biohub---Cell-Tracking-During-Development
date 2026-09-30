import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_exp211_d4_chunk_structure import validate


def row(name):
    return {
        "dataset": name,
        "edge_tp": 1,
        "edge_fp": 0,
        "edge_fn": 0,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "num_pred_nodes": 2,
        "node_recall": 1.0,
        "total_node_ratio": 1.0,
        "edge_jaccard": 1.0,
        "adj_edge_jaccard": 1.0,
    }


def write_metric(path, status, arms, movies):
    payload = {
        "status": status,
        "per_movie_by_arm": {arm: [row(name) for name in movies] for arm in arms},
        "summary_by_arm": {arm: {"score": 1.0} for arm in arms},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_run(tmp_path, direction="forward"):
    run = tmp_path / "run"
    results = run / "results"
    cache = results / "d4_raw_candidate_cache"
    cache.mkdir(parents=True)
    prefix = "6bba" if direction == "forward" else "44b6"
    movies = [f"{prefix}_a.zarr", f"{prefix}_b.zarr"]
    (run / "movies.json").write_text(json.dumps({"target_development": movies}), encoding="utf-8")
    write_metric(results / "d4_raw.json", "PASS_FROZEN_REGISTERED_MODEL_EVALUATION", ["registered_hungarian", "registered_weak_hungarian"], movies)
    minimum = "min8" if direction == "forward" else "min3"
    write_metric(results / "d4_filtered.json", "PASS_CACHED_SHORT_TRACK_FAMILY", ["no_filter", minimum], movies)
    for movie in movies:
        np.savez(cache / f"{Path(movie).stem}.npz", value=np.array([1]))
    return run


@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_valid_chunk_passes_without_metrics(direction, tmp_path):
    result = validate(make_run(tmp_path, direction), direction)
    assert result["status"] == "PASS_EXP211_D4_CHUNK_STRUCTURE_NO_METRICS"
    assert result["movie_count"] == 2
    assert result["scientific_metrics_emitted"] is False


def test_missing_cache_fails(tmp_path):
    run = make_run(tmp_path)
    next((run / "results" / "d4_raw_candidate_cache").glob("*.npz")).unlink()
    with pytest.raises(ValueError, match="cache coverage"):
        validate(run, "forward")

